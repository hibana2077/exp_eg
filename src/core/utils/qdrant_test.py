"""
Qdrant Test Script

This script verifies that the Qdrant integration works correctly.
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

def test_coordinate_search(client, embedding_model):
    """Test the coordinate search functionality with multi-vector format"""
    logger.info("Starting coordinate search test")
    
    # Create a test collection specifically for coordinate search
    coord_collection_name = f"{TEST_COLLECTION}_coordinate"
    
    try:
        # Delete if exists
        try:
            client.delete_collection(collection_name=coord_collection_name)
        except:
            pass
            
        # Create new collection with multi-vector format
        client.create_collection(
            collection_name=coord_collection_name,
            vectors_config={
                "embed": VectorParams(size=1024, distance=Distance.COSINE),
                "cord": VectorParams(size=4, distance=Distance.EUCLID)
            }
        )
        logger.info(f"Created coordinate test collection '{coord_collection_name}'")
        
        # Insert test data with coordinates
        coord_points = []
        for i, (text, embedding) in enumerate(zip(TEST_DATA, list(embedding_model.embed(TEST_DATA)))):
            # Create sample coordinates - in a real scenario, these would be bounding box coordinates
            # Format: [x1, y1, x2, y2]
            coord_vector = [i*0.1, i*0.2, i*0.1+0.5, i*0.2+0.5]
            
            coord_points.append(PointStruct(
                id=i,
                vector={
                    "embed": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    "cord": coord_vector
                },
                payload={
                    "text": text, 
                    "metadata": {"index": i}, 
                    "coord": coord_vector,
                    "page": 1
                }
            ))
        
        client.upsert(
            collection_name=coord_collection_name,
            points=coord_points
        )
        logger.info(f"Inserted {len(coord_points)} documents with coordinate vectors")
        
        # Test 1: Semantic search on multi-vector collection
        query = "artificial intelligence"
        query_embedding = list(embedding_model.embed([query]))[0]
        
        semantic_results = client.search(
            collection_name=coord_collection_name,
            query_vector=("embed", query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding),
            limit=2
        )
        
        logger.info(f"Semantic search for '{query}' returned {len(semantic_results)} results")
        if len(semantic_results) == 0:
            logger.error("Semantic search failed - no results returned")
            return False
            
        # Test 2: Coordinate search
        test_coord = [0.2, 0.4, 0.7, 0.9]  # Sample coordinate to search for
        
        coord_results = client.search(
            collection_name=coord_collection_name,
            query_vector=("cord", test_coord),
            limit=2
        )
        
        logger.info(f"Coordinate search returned {len(coord_results)} results")
        if len(coord_results) == 0:
            logger.error("Coordinate search failed - no results returned")
            return False
            
        # Test 3: Filter with coordinate search
        filter_results = client.search(
            collection_name=coord_collection_name,
            query_vector=("cord", test_coord),
            query_filter=Filter(
                must=[FieldCondition(key="page", match=MatchValue(value=1))]
            ),
            limit=2
        )
        
        logger.info(f"Filtered coordinate search returned {len(filter_results)} results")
        if len(filter_results) == 0:
            logger.error("Filtered coordinate search failed - no results returned")
            return False
        
        # Clean up
        client.delete_collection(collection_name=coord_collection_name)
        logger.info("Coordinate search test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Coordinate search test failed: {e}")
        try:
            client.delete_collection(collection_name=coord_collection_name)
        except:
            pass
        return False

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
        
    # Test multi-vector coordinate search functionality
    logger.info("Testing multi-vector coordinate search")
    multi_vector_test_result = test_coordinate_search(client, embedding_model)
    all_searches_successful = all_searches_successful and multi_vector_test_result
    
    # Skip the inline multi-vector test since we've already done it with the function
    
    # Create multi-vector collection
    multi_collection_name = f"{TEST_COLLECTION}_multi"
    try:
        # Delete if exists
        try:
            client.delete_collection(collection_name=multi_collection_name)
        except:
            pass
            
        client.create_collection(
            collection_name=multi_collection_name,
            vectors_config={
                "embed": VectorParams(size=1024, distance=Distance.COSINE),
                "cord": VectorParams(size=4, distance=Distance.EUCLID)
            }
        )
        
        # Insert test data with coordinates
        test_points = []
        for i, (text, embedding) in enumerate(zip(TEST_DATA, list(embedding_model.embed(TEST_DATA)))):
            # Create a simple dummy coordinate - in real data this would be meaningful
            test_coord = [i*0.1, i*0.2, i*0.3, i*0.4]  
            
            test_points.append(PointStruct(
                id=i,
                vector={
                    "embed": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    "cord": test_coord
                },
                payload={"text": text, "metadata": {"index": i}, "coord": test_coord}
            ))
        
        client.upsert(
            collection_name=multi_collection_name,
            points=test_points
        )
        logger.info(f"Inserted {len(test_points)} test documents with coordinates")
        
        # Test semantic search on multi-vector collection
        query_embedding = list(embedding_model.embed(["What is artificial intelligence?"]))[0]
        semantic_results = client.search(
            collection_name=multi_collection_name,
            query_vector=("embed", query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding),
            limit=2
        )
        
        logger.info(f"Multi-vector semantic search returned {len(semantic_results)} results")
        
        # Test coordinate search
        test_coord = [0.2, 0.4, 0.6, 0.8]
        coord_results = client.search(
            collection_name=multi_collection_name,
            query_vector=("cord", test_coord),
            limit=2
        )
        
        logger.info(f"Coordinate search returned {len(coord_results)} results")
        
        # Clean up
        client.delete_collection(collection_name=multi_collection_name)
        return True
    except Exception as e:
        logger.error(f"Multi-vector test failed: {e}")
        try:
            client.delete_collection(collection_name=multi_collection_name)
        except:
            pass
        return False
    
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
