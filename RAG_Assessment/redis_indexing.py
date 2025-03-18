import os
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import (
    DocstoreStrategy,
    IngestionPipeline,
    IngestionCache,
)
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.redis import RedisVectorStore
from redisvl.schema import IndexSchema
from config_loader import load_shared_resources
import logging
from llama_cloud_services import LlamaParse

def create_ingestion_pipeline(embed_model, custom_schema):
    """Creates and returns the ingestion pipeline."""
    return IngestionPipeline(
        transformations=[
            SentenceSplitter(),
            embed_model,
        ],
        docstore=RedisDocumentStore.from_host_and_port(
            "localhost", 6379, namespace="document_store"
        ),
        vector_store=RedisVectorStore(
            schema=custom_schema,
            redis_url="redis://localhost:6379",
        ),
        cache=IngestionCache(
            cache=RedisCache.from_host_and_port("localhost", 6379),
            collection="redis_cache",
        ),
        docstore_strategy=DocstoreStrategy.UPSERTS,
    )

def load_documents(data_dir="./data"):
    """(Unchanged) Loads documents from a local directory."""
    parser = LlamaParse(result_type="markdown")
    file_extractor = {".pdf": parser}

    logging.info("Loading documents...")
    documents = SimpleDirectoryReader(
        data_dir, filename_as_id=True, file_extractor=file_extractor
    ).load_data()
    logging.info(f"Documents loaded: {len(documents)}")
    if documents:
        logging.info(f"First document loaded: {documents[0]}")
    else:
        logging.warning("No documents loaded from directory!")
    return documents

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

def run_indexing():
    """(Unchanged) Loads documents from ./data and indexes them."""
    config, embed_model = load_shared_resources()
    documents = load_documents()
    if not documents:
        logging.warning("No documents to index. Exiting indexing process.")
        return

    custom_schema = define_custom_schema()
    pipeline = create_ingestion_pipeline(embed_model, custom_schema)
    nodes = pipeline.run(documents=documents)
    logging.info(f"Ingested {len(nodes)} Nodes")
    print(f"Ingested {len(nodes)} Nodes")  # for direct script execution

def run_indexing_with_files(file_paths, embed_model):
    """
    New helper function to index user-uploaded files.

    1. Parse each file with LlamaParse.  
    2. Use the same ingestion pipeline logic (SentenceSplitter + embed_model).  
    3. Return the number of ingested nodes.
    """
    # Prepare for PDF parsing
    parser = LlamaParse(result_type="markdown")
    file_extractor = {".pdf": parser}
    documents = []

    # Parse each uploaded file
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            # Load data using the parser
            single_doc_reader = SimpleDirectoryReader(
                input_files=[file_path],
                filename_as_id=True,
                file_extractor=file_extractor
            )
            docs_out = single_doc_reader.load_data()
            documents.extend(docs_out)
        else:
            logging.warning(f"File {file_path} is not a PDF, skipping.")

    if not documents:
        raise ValueError("No valid PDF documents to index.")
    
    # Create pipeline exactly as in run_indexing()
    custom_schema = define_custom_schema()
    pipeline = create_ingestion_pipeline(embed_model, custom_schema)
    
    # Run the pipeline on the newly parsed documents
    nodes = pipeline.run(documents=documents)
    logging.info(f"Ingested {len(nodes)} Node(s) from uploaded files.")
    return len(nodes)

if __name__ == "__main__":
    run_indexing()
    logging.info("Indexing process completed.")