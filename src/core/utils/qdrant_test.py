"""
Qdrant Test Script

This script verifies that the Qdrant integration is working correctly.
It performs basic operations:
1. Connects to Qdrant
2. Creates a test collection
3. Inserts test data
4. Performs a search
5. Cleans up

Run this script in the core container:
docker-compose exec core python /app/utils/qdrant_test.py
"""

import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("qdrant-test")

# Test config
TEST_COLLECTION = "test_qdrant_integration"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"  # Same as in cfg/emb_settings.py
TEST_DATA = [
    "This is a test document about artificial intelligence.",
    "Vector databases are used for similarity search.",
    "Qdrant is a vector database designed for production use.",
    "Python is a programming language used for data science.",
    "Machine learning models can be deployed in various environments."
]
TEST_QUERIES = [
    "What is artificial intelligence?",
    "How are vector databases used?",
    "Tell me about Qdrant."
]

def main():
    """Run the Qdrant test suite"""
    logger.info("Starting Qdrant test")
    
    # Get Qdrant configuration from environment
    qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize Qdrant client
    logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        logger.info("Connected to Qdrant successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return False
    
    # Clean up any existing test collection
    try:
        collections = client.get_collections().collections
        for collection in collections:
            if collection.name == TEST_COLLECTION:
                logger.info(f"Removing existing test collection '{TEST_COLLECTION}'")
                client.delete_collection(collection_name=TEST_COLLECTION)
    except Exception as e:
        logger.warning(f"Error checking for existing collections: {e}")
    
    # Create test collection
    logger.info(f"Creating test collection '{TEST_COLLECTION}'")
    try:
        client.create_collection(
            collection_name=TEST_COLLECTION,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        logger.info("Test collection created successfully")
    except Exception as e:
        logger.error(f"Failed to create test collection: {e}")
        return False
    
    # Initialize embedding model
    logger.info(f"Loading embedding model '{EMBEDDING_MODEL}'")
    try:
        embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        client.delete_collection(collection_name=TEST_COLLECTION)
        return False
    
    # Generate embeddings and insert test data
    logger.info("Generating embeddings and inserting test data")
    try:
        embeddings = list(embedding_model.embed(TEST_DATA))
        points = []
        
        for i, (text, embedding) in enumerate(zip(TEST_DATA, embeddings)):
            points.append(PointStruct(
                id=i,
                vector=embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                payload={"text": text, "metadata": {"index": i}}
            ))
        
        client.upsert(
            collection_name=TEST_COLLECTION,
            points=points
        )
        logger.info(f"Inserted {len(points)} test documents successfully")
    except Exception as e:
        logger.error(f"Failed to insert test data: {e}")
        client.delete_collection(collection_name=TEST_COLLECTION)
        return False
    
    # Test search functionality
    logger.info("Testing search functionality")
    all_searches_successful = True
    
    for query in TEST_QUERIES:
        try:
            logger.info(f"Searching for: '{query}'")
            query_embedding = list(embedding_model.embed([query]))[0]
            
            search_results = client.search(
                collection_name=TEST_COLLECTION,
                query_vector=query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding,
                limit=2
            )
            
            logger.info(f"Search returned {len(search_results)} results")
            for i, result in enumerate(search_results):
                logger.info(f"  Result {i+1}: Score={result.score:.4f}, Text='{result.payload['text']}'")
            
            if not search_results:
                logger.error("Search returned no results")
                all_searches_successful = False
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            all_searches_successful = False
    
    # Test filtering
    logger.info("Testing filtering functionality")
    try:
        filter_results = client.search(
            collection_name=TEST_COLLECTION,
            query_vector=embeddings[0].tolist() if hasattr(embeddings[0], 'tolist') else embeddings[0],
            query_filter=Filter(
                must=[FieldCondition(key="metadata.index", match=MatchValue(value=1))]
            ),
            limit=5
        )
        
        logger.info(f"Filter search returned {len(filter_results)} results")
        for i, result in enumerate(filter_results):
            logger.info(f"  Result {i+1}: Id={result.id}, Score={result.score:.4f}")
            
        if not filter_results or filter_results[0].id != 1:
            logger.error("Filter search did not return expected result")
            all_searches_successful = False
            
    except Exception as e:
        logger.error(f"Filter search failed: {e}")
        all_searches_successful = False
    
    # Clean up
    logger.info(f"Cleaning up test collection '{TEST_COLLECTION}'")
    try:
        client.delete_collection(collection_name=TEST_COLLECTION)
        logger.info("Test collection deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete test collection: {e}")
    
    # Report results
    if all_searches_successful:
        logger.info("✅ All tests passed! Qdrant integration is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Check logs for details.")
        return False

if __name__ == "__main__":
    main()
