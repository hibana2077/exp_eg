import datetime
import os
import pymongo
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from .mongo_atlas_config import get_db_collection, MONGO_ATLAS_ENABLED

def indexing(db_name:str, table_name:str, use_atlas: Optional[bool] = None):
    """
    Create indices for MongoDB collections.
    
    Args:
        db_name: Database name
        table_name: Collection/table name
        use_atlas: If True, use MongoDB Atlas; if False, use local MongoDB;
                  if None (default), use the MONGO_ATLAS_ENABLED environment variable
    
    Returns:
        Name of the created index
    """
    print("Check Point A: ", datetime.datetime.now())
    
    # Get the database collection from either Atlas or local MongoDB
    collection, is_atlas = get_db_collection(db_name, table_name, use_atlas)
    
    # Create a text index for text search
    index_name = 'text_index_in_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create text index on the 'text' field
    collection.create_index([('text', pymongo.TEXT)], name=index_name)
    
    # Create indexes for vector search (assuming 'embedding' field exists)
    try:
        # For MongoDB Atlas vector search
        vector_index_config = {
            "name": "embedding_vector_index",
            "type": "vectorSearch",
            "fields": [
                {
                    "path": "embedding",
                    "numDimensions": 512,  # Adjust dimension to match your embeddings
                    "similarity": "cosine"  # Options: cosine, dotProduct, euclidean
                }
            ]
        }
        
        # Create vector search index via Atlas command
        # Note: This command is for reference only as it normally requires Atlas UI or API
        # In practice, you'd create these indexes through the MongoDB Atlas interface or API
        # db.runCommand({ "createSearchIndexes": table_name, "indexes": [vector_index_config] })
        
        print(f"MongoDB index creation completed: {index_name}")
    except Exception as e:
        print(f"Warning: Vector index creation may require MongoDB Atlas UI configuration: {e}")
    
    return index_name

def add_index_into_condiction(condiction, index_name:str):
    # In MongoDB, we don't need to specify index name for queries
    # But we'll keep this function for compatibility with existing code
    text_condictions = condiction.get("text", [])
    for cond in text_condictions:
        cond['options'] = {'index_name': index_name}
    return condiction