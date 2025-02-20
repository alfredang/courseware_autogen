import os
import yaml
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.extractors import QuestionsAnsweredExtractor
from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    SentenceSplitter,
)
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.schema import (
    NodeRelationship,
    RelatedNodeInfo,
    TextNode,
)
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.storage.docstore.firestore import FirestoreDocumentStore
from pydantic import BaseModel
import chromadb
from tqdm.asyncio import tqdm_asyncio
import asyncio
import logging
from typing import List
from llama_index.core.prompts import PromptTemplate  # Correct import
from llama_index.readers.file import PDFReader
from dotenv import load_dotenv
import hashlib  # Import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path, override=True)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path) as config_file:
        return yaml.safe_load(config_file)

config = load_config()
CHUNK_SIZES = config["chunk_sizes"]
CHUNK_SIZE = config.get("chunk_size", 512)
CHUNK_OVERLAP = config.get("chunk_overlap", 50)
INDEXING_METHOD = config["indexing_method"]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FIRESTORE_DB_NAME = config.get("firestore_db_name", "(default)")
FIRESTORE_NAMESPACE = config.get("firestore_namespace", None)
GOOGLE_APPLICATION_CREDENTIALS = "assessment-rag-b43dc08b8535.json"

# --- Define Prompts (Corrected) ---
QA_EXTRACTION_PROMPT = PromptTemplate(
    template="""\
Here is the context:
---------------------
{context_str}
---------------------
Given the contextual information, generate 5 questions this document can answer.\
"""
)

QA_PARSER_PROMPT = PromptTemplate(
    template="""\
Here is a list of questions:
---------------------
{questions_list}
---------------------
Format this into a JSON that can be parsed by pydantic, and answer with the format:
{{
    "questions_list": [list of questions]
}}
"""
)

class QuesionsAnswered(BaseModel):
    """List of Questions Answered by Document"""
    questions_list: List[str]

def generate_doc_id(document: Document) -> str:
    """Generates a unique ID for a document based on its content and filename."""
    combined_content = document.text + document.metadata.get("filename", "")
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()


async def create_qa_index(li_docs, docstore, embed_model, llm):
    """Creates an index of hypothetical questions."""

    qa_extractor = QuestionsAnsweredExtractor(
        llm=llm, questions=5, prompt_template=QA_EXTRACTION_PROMPT  # Corrected
    )

    async def extract_batch(li_docs):
        return await tqdm_asyncio.gather(
            *[qa_extractor.aextract(doc) for doc in li_docs]  # Corrected: Use aextract
        )

    metadata_list = await extract_batch(li_docs)


    program = LLMTextCompletionProgram.from_defaults(
        output_cls=QuesionsAnswered,
        prompt_template_str=QA_PARSER_PROMPT.template, # Pass template string
        llm=llm,
        verbose=True,
    )

    async def parse_batch(metadata_list):
        return await asyncio.gather(
            *[program.acall(questions_list=x) for x in metadata_list],  # Corrected: questions_list
            return_exceptions=True,
        )

    parsed_questions = await parse_batch(metadata_list)

    q_docs = []
    for doc, questions in zip(li_docs, parsed_questions):
        if isinstance(questions, Exception):
            logger.info(f"Unparsable questions exception {questions}")
            continue
        elif questions and questions.questions_list:
            for q in questions.questions_list:
                logger.info(f"Question extracted: {q}")
                q_doc = Document(text=q)
                q_doc.doc_id = generate_doc_id(q_doc) # Generate and set doc_id
                q_doc.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                    node_id=doc.doc_id  # This will also be a hash now.
                )
                q_docs.append(q_doc)

    # Add to docstore, checking for existing documents
    for q_doc in q_docs:
        existing_doc = docstore.get_document(q_doc.doc_id)
        if existing_doc:
            logger.info(f"Skipping question document with ID {q_doc.doc_id} (already exists).")
            continue  # Skip to the next document
        docstore.add_documents([q_doc])

    # Add the *original* documents (after setting their IDs)
    for doc in li_docs:
        existing_doc = docstore.get_document(doc.doc_id)
        if existing_doc:
            logger.info(f"Skipping original document with ID {doc.doc_id} (already exists).")
            continue
        docstore.add_documents([doc])


    chroma_client = chromadb.PersistentClient(path="./chroma_db_qa")
    chroma_collection = chroma_client.get_or_create_collection("qa_collection")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )
    VectorStoreIndex(
        nodes=q_docs,
        storage_context=storage_context,
        embed_model=embed_model,
        llm=llm,
    )

def create_hierarchical_index(li_docs, docstore, vector_store, embed_model, llm):
    """Creates a hierarchical index."""

    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=CHUNK_SIZES)
    nodes = node_parser.get_nodes_from_documents(li_docs)

    leaf_nodes = [node for node in nodes if NodeRelationship.CHILD not in node.relationships]
    num_leaf_nodes = len(leaf_nodes)
    num_nodes = len(nodes)
    logger.info(f"There are {num_leaf_nodes} leaf_nodes and {num_nodes} total nodes")

    # Add to docstore, checking for existing documents FIRST
    for node in nodes:
        node.doc_id = generate_doc_id(node) # Generate and set doc_id
        existing_doc = docstore.get_document(node.doc_id)
        if existing_doc:
            logger.info(f"Skipping node with ID {node.doc_id} (already exists).")
            continue # Skip to the next node.
        docstore.add_documents([node])

    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )
    VectorStoreIndex(
        nodes=leaf_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        llm=llm,
    )

def create_flat_index(li_docs, docstore, vector_store, embed_model, llm):
    """Creates a flat index."""
    sentence_splitter = SentenceSplitter(chunk_size=CHUNK_OVERLAP)
    node_chunk_list = []
    for doc in li_docs:
        doc_dict = doc.to_dict()
        metadata = doc_dict.pop("metadata")
        doc_dict.update(metadata)
        chunks = sentence_splitter.get_nodes_from_documents([doc])

        nodes = []
        for chunk in chunks:
            text = chunk.text
            doc_source_id = doc.doc_id  # This will already be the hash
            node = TextNode(text=text, metadata=chunk.metadata)
            node.doc_id = generate_doc_id(node) # Generate and set doc_id for the NODE
            node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                node_id=doc_source_id
            )
            nodes.append(node)

        node_chunk_list.extend(nodes)

    nodes = node_chunk_list
    logger.info("embedding...")

    # Add to docstore, checking for existing documents FIRST
    for node in nodes:
        existing_doc = docstore.get_document(node.doc_id)
        if existing_doc:
            logger.info(f"Skipping node with ID {node.doc_id} (already exists).")
            continue
        docstore.add_documents([node])


    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )

    VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        llm=llm,
    )


def load_docs_from_directory(directory_path: str) -> List[Document]:
    """Loads documents from a directory, handling PDFs and TXTs."""
    documents = []
    loader = PDFReader()

    for filename in os.listdir(directory_path):
        if filename.startswith("."):
            continue
        filepath = os.path.join(directory_path, filename)
        try:
            if filename.lower().endswith(".pdf"):
                docs = loader.load_data(file=filepath)
                for doc in docs:
                    doc.metadata["filename"] = filename
                    # Set the doc_id *immediately* after loading
                    doc.doc_id = generate_doc_id(doc)
                    documents.append(doc)
            elif filename.lower().endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                    doc = Document(text=text, metadata={"filename": filename})
                    # Set the doc_id *immediately* after loading
                    doc.doc_id = generate_doc_id(doc)
                    documents.append(doc)
            else:
                logger.warning(f"Skipping unsupported file type: {filename}")

        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")

    return documents

def main():
    """Main function to run the indexing pipeline."""
    documents = load_docs_from_directory("./data")
    if not documents:
        logger.error("No documents loaded. Exiting.")
        return

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004", api_key=GEMINI_API_KEY  #Corrected model
    )
    llm = Gemini(api_key=GEMINI_API_KEY, model_name="models/gemini-2.0-flash-exp", temperature=0.0) #Corrected Model

    Settings.llm = llm
    Settings.embed_model = embed_model

    chroma_client = chromadb.PersistentClient(path="./chroma_db_main")
    chroma_collection = chroma_client.get_or_create_collection("main_collection")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    docstore = FirestoreDocumentStore.from_database(
        project=config["project_id"], database=FIRESTORE_DB_NAME, namespace=FIRESTORE_NAMESPACE
    )

    if config.get("create_qa_index_flag", False):
        asyncio.run(create_qa_index(documents, docstore, embed_model, llm))

    if config.get("create_vector_index_flag", True):
        if INDEXING_METHOD == "hierarchical":
            create_hierarchical_index(documents, docstore, vector_store, embed_model, llm)
        elif INDEXING_METHOD == "flat":
            create_flat_index(documents, docstore, vector_store, embed_model, llm)
        else:
            logger.error(f"Invalid indexing method: {INDEXING_METHOD}")

    print("Indexing complete (local, using Gemini API).")

if __name__ == "__main__":
    main()