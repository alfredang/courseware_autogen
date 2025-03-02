from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.llms import ChatMessage
from llama_index.vector_stores.redis import RedisVectorStore
from redisvl.schema import IndexSchema
from llama_index.core.query_pipeline import (
    QueryPipeline,
    CustomQueryComponent
)
from llama_index.llms.gemini import Gemini
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_pipeline.components.input import InputComponent
from typing import Optional, List, Dict, Any
from pydantic import Field
from llama_index.core.schema import NodeWithScore

DEFAULT_CONTEXT_PROMPT = (
    "Here is some context that may be relevant:\n"
    "-----\n"
    "{node_context}\n"
    "-----\n"
    "Please write a response to the following question, using the above context:\n"
    "{query_str}\n"
)

def define_custom_schema():
    """Defines the custom Redis index schema."""
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
                        "dims": 384,
                        "algorithm": "hnsw",
                        "distance_metric": "cosine",
                    },
                },
            ],
        }
    )

class MergeNodesComponent(CustomQueryComponent):
    """Custom component that merges node lists from multiple retrievers."""
    
    top_k: int = Field(default=8, description="Number of top nodes to return")
    
    @property
    def _input_keys(self) -> set:
        return {"rewrite_nodes", "query_nodes"}

    @property
    def _output_keys(self) -> set:
        return {"nodes"}

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        rewrite_nodes = kwargs.get("rewrite_nodes", [])
        query_nodes = kwargs.get("query_nodes", [])
        
        # Combine nodes from both retrievers
        node_dict = {}
        for node in rewrite_nodes + query_nodes:
            if node.node_id not in node_dict:
                node_dict[node.node_id] = node
        
        all_nodes = list(node_dict.values())
        all_nodes.sort(key=lambda x: x.score if hasattr(x, 'score') and x.score is not None else 0, reverse=True)
        all_nodes = all_nodes[:self.top_k]
        
        return {"nodes": all_nodes}

class ResponseWithChatHistory(CustomQueryComponent):
    llm: Gemini = Field(..., description="Gemini LLM")
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
        return input

    @property
    def _input_keys(self) -> set:
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
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(
            chat_history, nodes, query_str
        )

        response = self.llm.chat(prepared_context)
        return {"response": response}

def initialize_chat_pipeline(embed_model, config):
    """Initialize the chat pipeline with the given embedding model and configuration."""
    llm = Gemini(
        api_key=config.get("gemini_api_key") or config.get("GEMINI_API_KEY") or config.get("GEMINI_API"), 
        model_name=config.get("llm_model", "gemini-1.5-pro")
    )
    
    custom_schema = define_custom_schema()
    vector_store = RedisVectorStore(
        schema=custom_schema, redis_url="redis://localhost:6379"
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=embed_model
    )

    # Input Component
    input_component = InputComponent()

    # Rewrite Component
    rewrite_template = PromptTemplate(
        "Please write a query to a semantic search engine using the current conversation.\n"
        "\n"
        "{chat_history_str}"
        "\n"
        "\n"
        "Latest message: {query_str}\n"
        'Query:"""\n'
    )

    # Retrievers
    retriever = VectorIndexRetriever(index=index, similarity_top_k=6)

    # Response Component
    response_component = ResponseWithChatHistory(
        llm=llm,
        system_prompt=(
            "You are a helpful assistant that answers questions based on the provided document context. "
            "When you don't know the answer based on the provided context, say so clearly. "
            "Provide comprehensive answers, but avoid speculation beyond what's in the context."
        ),
    )
    
    # Merge Component
    merge_component = MergeNodesComponent()
    
    # Define Pipeline Modules
    modules = {
        "input": input_component,
        "rewrite_template": rewrite_template,
        "llm": llm,
        "rewrite_retriever": retriever,
        "query_retriever": retriever,
        "join": merge_component,
        "response_component": response_component,
    }

    # Create Query Pipeline
    pipeline = QueryPipeline(modules=modules, verbose=False)

    # Define Pipeline Links
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

def run_chat_query(query_text, query_pipeline, pipeline_memory, retrieval_mode="hybrid", top_k=6):
    """Run a chat query with the given pipeline and memory."""
    # Get memory
    chat_history = pipeline_memory.get()

    # Format chat history for string representation
    chat_history_str = "\n".join([str(x) for x in chat_history])

    # Run the query
    response = query_pipeline.run(
        query_str=query_text,
        chat_history=chat_history,
        chat_history_str=chat_history_str,
    )

    # Update memory
    user_msg = ChatMessage(role="user", content=query_text)
    pipeline_memory.put(user_msg)
    pipeline_memory.put(response.message)

    return response