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
from llama_cloud_services import LlamaParse
import redis

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

def create_ingestion_pipeline(embed_model, custom_schema, chunk_size=3, chunk_overlap=1):
    """Creates and returns the ingestion pipeline with configurable chunking."""
    return IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
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

def load_documents_from_files(file_paths):
    """Loads documents from the specified file paths."""
    parser = LlamaParse(result_type="markdown")
    file_extractor = {".pdf": parser}
    
    documents = []
    for file_path in file_paths:
        doc = SimpleDirectoryReader(
            input_files=[file_path],
            filename_as_id=True,
            file_extractor=file_extractor
        ).load_data()
        documents.extend(doc)
    
    return documents

def run_indexing_with_files(file_paths, embed_model, chunk_size=3, chunk_overlap=1):
    """Runs the indexing pipeline with the specified files."""
    documents = load_documents_from_files(file_paths)
    if not documents:
        raise ValueError("No documents could be loaded from the provided files")
    
    custom_schema = define_custom_schema()
    pipeline = create_ingestion_pipeline(
        embed_model, 
        custom_schema,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    nodes = pipeline.run(documents=documents)
    return len(nodes)

def check_index_status():
    """Check if the index exists and return its status."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        keys = r.keys("doc:*")
        node_count = len(keys)
        
        # Get stats about the index
        stats = {
            "total_keys": node_count,
            "document_keys": len(r.keys("doc:document:*")),
            "node_keys": len(r.keys("doc:vector:*")),
            "memory_usage": r.info("memory")["used_memory_human"],
        }
        
        return {
            "exists": node_count > 0,
            "node_count": node_count,
            "stats": stats
        }
    except Exception as e:
        return {
            "exists": False,
            "node_count": 0,
            "stats": {"error": str(e)},
        }