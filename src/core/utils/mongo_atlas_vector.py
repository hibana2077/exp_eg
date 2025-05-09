"""
MongoDB Atlas Vector Search Utilities

This module provides helper functions for working with MongoDB Atlas vector search.
Note: Some operations require MongoDB Atlas and may not work with a standard MongoDB installation.
"""

import pymongo
import logging
import json
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def create_vector_search_index(
    client: pymongo.MongoClient,
    database_name: str,
    collection_name: str, 
    vector_field: str,
    dimensions: int = 512,
    similarity: str = "cosine"
) -> Dict[str, Any]:
    """
    Create a vector search index on a MongoDB Atlas collection.
    
    Note: This function creates a configuration for Atlas vector search.
    In a production environment, you would typically create these indexes
    through the MongoDB Atlas UI or API.
    
    Args:
        client: PyMongo client connected to MongoDB Atlas
        database_name: Name of the database
        collection_name: Name of the collection
        vector_field: Field containing vector embeddings
        dimensions: Dimensionality of the vector embeddings
        similarity: Similarity metric (cosine, dotProduct, euclidean)
        
    Returns:
        Dictionary with status information
    """
    # Vector search index configuration
    index_name = f"{vector_field}_vector_idx"
    
    # This is the configuration structure for Atlas vector search
    vector_search_config = {
        "name": index_name,
        "type": "vectorSearch",
        "fields": [
            {
                "path": vector_field,
                "numDimensions": dimensions,
                "similarity": similarity
            }
        ]
    }
    
    logger.info(f"Creating vector search index '{index_name}' on {database_name}.{collection_name}")
    
    try:
        # In a real Atlas environment, you would use:
        # db = client[database_name]
        # result = db.command({
        #     "createSearchIndexes": collection_name,
        #     "indexes": [vector_search_config]
        # })
        
        # For now, just log the configuration that would be used
        logger.info(f"Vector search index config: {json.dumps(vector_search_config, indent=2)}")
        
        return {
            "status": "success",
            "message": "Vector search index configuration generated",
            "note": "In MongoDB Atlas, you need to create this index through the Atlas UI or API",
            "index_name": index_name,
            "config": vector_search_config
        }
    except Exception as e:
        logger.error(f"Error creating vector search index: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def vector_search_query(
    collection,
    vector_field: str,
    query_vector: List[float],
    limit: int = 10,
    additional_filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Generate a MongoDB aggregation pipeline for vector search.
    
    Args:
        collection: MongoDB collection
        vector_field: Field containing vector embeddings
        query_vector: Vector to search for
        limit: Maximum number of results
        additional_filters: Additional query filters
        
    Returns:
        Results from the vector search
    """
    # Build the aggregation pipeline
    pipeline = []
    
    # Add any filters first
    if additional_filters:
        pipeline.append({"$match": additional_filters})
    
    # Add vector search using $vectorSearch
    pipeline.append({
        "$vectorSearch": {
            "index": f"{vector_field}_vector_idx",
            "path": vector_field,
            "queryVector": query_vector,
            "numCandidates": limit * 10,  # Increased for better recall
            "limit": limit
        }
    })
    
    # Add a projection to include the score
    pipeline.append({
        "$project": {
            "_id": 1,
            "score": {"$meta": "searchScore"},
            # Include all other fields
            "text": 1,
            "embedding": 1,
            "self_ref": 1,
            "parent": 1,
            "content_layer": 1,
            "label": 1,
            "page": 1,
            "coord": 1,
            "coord_origin": 1
        }
    })
    
    # Execute the pipeline
    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        logger.error(f"Vector search error: {str(e)}")
        # Fall back to simpler approach if $vectorSearch isn't available
        logger.info("Falling back to basic document retrieval without vector search")
        return list(collection.find({}, limit=limit))
