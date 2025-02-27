# query_chain.py
from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.llms import ChatMessage
from llama_index.vector_stores.redis import RedisVectorStore
from redisvl.schema import IndexSchema
from config_loader import load_shared_resources
from llama_index.core.query_pipeline import (
    QueryPipeline,
    ArgPackComponent,
    CustomQueryComponent
)
from llama_index.llms.gemini import Gemini
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import TreeSummarize
from llama_index.core.memory import ChatMemoryBuffer
from typing import Optional, List, Dict, Any
from pydantic import Field
from llama_index.core.schema import NodeWithScore
import logging
from llama_index.core.query_pipeline.components.input import InputComponent


def define_custom_schema():
    """Defines the custom Redis index schema - MUST MATCH indexing schema."""
    return IndexSchema.from_dict(
        {
            "index": {"name": "redis_vector_store", "prefix": "doc"},
            "fields": [
                {"type": "tag", "name": "id"},
                {"type": "tag", "name": "doc_id"},
                {"type": "text", "name": "text"},
                {"type": "numeric", "name": "updated_at"},
                {"type": "tag", "name": "file_name"},
                {
                    "type": "vector",
                    "name": "vector",
                    "attrs": {
                        "dims": 384,  # MUST match indexing schema
                        "algorithm": "hnsw",
                        "distance_metric": "cosine",
                    },
                },
            ],
        }
    )


DEFAULT_CONTEXT_PROMPT = (
    "Here is some context that may be relevant:\n"
    "-----\n"
    "{node_context}\n"
    "-----\n"
    "Please write a response to the following question, using the above context:\n"
    "{query_str}\n"
)

class MergeNodesComponent(CustomQueryComponent):
    """Custom component that merges node lists from multiple retrievers."""
    
    @property
    def _input_keys(self) -> set:
        return {"rewrite_nodes", "query_nodes"}

    @property
    def _output_keys(self) -> set:
        return {"nodes"}  # Use "nodes" directly as output key to match response_component's expected input

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        rewrite_nodes = kwargs.get("rewrite_nodes", [])
        query_nodes = kwargs.get("query_nodes", [])
        
        # Combine nodes from both retrievers
        # Use a dictionary with node IDs as keys to remove duplicates
        node_dict = {}
        for node in rewrite_nodes + query_nodes:
            if node.node_id not in node_dict:
                node_dict[node.node_id] = node
        
        # Get the combined list of nodes
        all_nodes = list(node_dict.values())
        
        # Sort by score if available (optional)
        all_nodes.sort(key=lambda x: x.score if hasattr(x, 'score') and x.score is not None else 0, reverse=True)
        
        # Take top-k nodes (optional, adjust as needed)
        top_k = 8  # Adjust based on your needs
        all_nodes = all_nodes[:top_k]
        
        return {"nodes": all_nodes}

class ResponseWithChatHistory(CustomQueryComponent):
    llm: Gemini = Field(..., description="Gemini LLM")  # Use Gemini LLM
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt to use for the LLM"
    )
    context_prompt: str = Field(
        default=DEFAULT_CONTEXT_PROMPT,
        description="Context prompt to use for the LLM",
        )


    def _validate_component_inputs(
        self, input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        return {"chat_history", "nodes", "query_str"}

    @property
    def _output_keys(self) -> set:
        return {"response"}

    def _prepare_context(
        self,
        chat_history: List[ChatMessage],
        nodes: List[NodeWithScore],
        query_str: str,
    ) -> List[ChatMessage]:
        node_context = ""
        for idx, node in enumerate(nodes):
            node_text = node.get_content(metadata_mode="llm")
            node_context += f"Context Chunk {idx}:\n{node_text}\n\n"

        formatted_context = self.context_prompt.format(
            node_context=node_context, query_str=query_str
        )
        user_message = ChatMessage(role="user", content=formatted_context)

        chat_history.append(user_message)

        if self.system_prompt is not None:
            chat_history = [
                ChatMessage(role="system", content=self.system_prompt)
            ] + chat_history

        return chat_history

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(
            chat_history, nodes, query_str
        )

        response = self.llm.chat(prepared_context) # Use self.llm to call Gemini

        return {"response": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(
            chat_history, nodes, query_str
        )

        response = await self.llm.achat(prepared_context) # Use self.llm to call Gemini

        return {"response": response}


def create_complex_query_pipeline(embed_model, llm):
    """Creates and returns the complex query pipeline with memory and Gemini LLM."""
    custom_schema = define_custom_schema()
    vector_store = RedisVectorStore(
        schema=custom_schema, redis_url="redis://localhost:6379"
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=embed_model
    )

    # Input Component
    input_component = InputComponent()

    # Rewrite Component (Prompt Template)
    rewrite_template = PromptTemplate(
        "Please write a query to a semantic search engine using the current conversation.\n"
        "\n"
        "\n"
        "{chat_history_str}"
        "\n"
        "\n"
        "Latest message: {query_str}\n"
        'Query:"""\n'
    )

    # ArgPack Component
    argpack_component = ArgPackComponent()

    # Retrievers (using the index)
    retriever = VectorIndexRetriever(index=index, similarity_top_k=6) # Adjust top_k as needed

    # Response Component (Custom - adapted for Gemini)
    response_component = ResponseWithChatHistory(
        llm=llm, # Pass the Gemini LLM instance
        system_prompt=(
            "You are a Q&A system. You will be provided with the previous chat history, "
            "as well as possibly relevant context, to assist in answering a user message."
        ),
    )
    merge_component = MergeNodesComponent()
    # Define Pipeline Modules
    modules = {
        "input": input_component,
        "rewrite_template": rewrite_template,
        "llm": llm, # Pass LLM to modules for pipeline access
        "rewrite_retriever": retriever,
        "query_retriever": retriever,
        "join": merge_component,
        "response_component": response_component,
    }

    # Create Query Pipeline
    pipeline = QueryPipeline(modules=modules, verbose=False)

    # Define Pipeline Links (without reranker for now)
    pipeline.add_link(
        "input", "rewrite_template", src_key="query_str", dest_key="query_str"
    )
    pipeline.add_link(
        "input",
        "rewrite_template",
        src_key="chat_history_str",
        dest_key="chat_history_str",
    )
    pipeline.add_link("rewrite_template", "llm")
    pipeline.add_link("llm", "rewrite_retriever")
    pipeline.add_link("input", "query_retriever", src_key="query_str")

    pipeline.add_link("rewrite_retriever", "join", dest_key="rewrite_nodes")
    pipeline.add_link("query_retriever", "join", dest_key="query_nodes")

    pipeline.add_link("join", "response_component", dest_key="nodes")
    pipeline.add_link(
        "input", "response_component", src_key="query_str", dest_key="query_str"
    )
    pipeline.add_link(
        "input",
        "response_component",
        src_key="chat_history",
        dest_key="chat_history",
    )

    return pipeline


def run_query(query_text, query_pipeline, pipeline_memory): # Pass pipeline and memory
    """Runs a query against the index using the complex query pipeline and prints the response."""
    # get memory
    chat_history = pipeline_memory.get()

    # prepare inputs
    chat_history_str = "\n".join([str(x) for x in chat_history])

    # run pipeline
    response = query_pipeline.run(
        query_str=query_text,
        chat_history=chat_history,
        chat_history_str=chat_history_str,
    )

    # update memory
    user_msg = ChatMessage(role="user", content=query_text)
    pipeline_memory.put(user_msg)
    pipeline_memory.put(response.message)

    print(f"User Query: {query_text}")
    print(f"Gemini Response: {response.message.content}") # Print content from response message
    logging.info(f"Query: {query_text} - Response received from Complex Query Pipeline (query_chain.py).")
    return response


def main(): # Encapsulate main execution logic in a function
    config, embed_model = load_shared_resources()
    llm = Gemini(api_key=config.get("gemini_api_key") or config.get("GEMINI_API_KEY") or config.get("GEMINI_API"), model_name=config.get("llm_model")) # Re-initialize Gemini LLM

    query_pipeline = create_complex_query_pipeline(embed_model, llm)
    pipeline_memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

    user_inputs = [
        "Hello!",
        "When was Lena Yeo employed?",
        "Who is writing the letter on Lena's behalf?",
        "What is the role of Lena Yeo?",
    ]

    for msg in user_inputs:
        run_query(msg, query_pipeline, pipeline_memory) # Pass pipeline and memory to run_query
        print() # Add newline for readability


if __name__ == "__main__":
    main() # Call main function to run queries
    logging.info("Complex query pipeline process completed (query_chain.py).")