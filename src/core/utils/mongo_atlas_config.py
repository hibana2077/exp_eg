"""
MongoDB Configuration

This module provides configuration values and utility functions for MongoDB and MongoDB Atlas integration.
It supports using both MongoDB Atlas (cloud/production) and a local MongoDB instance (development/testing).
"""

import os
import pymongo
from typing import Dict, Any, Optional, Tuple

# Feature flag to enable/disable MongoDB Atlas
MONGO_ATLAS_ENABLED = os.getenv("MONGO_ATLAS_ENABLED", "false").lower() == "true"

# MongoDB Atlas Connection (Cloud database)
MONGO_ATLAS_CONNECTION_STRING = os.getenv("MONGO_ATLAS_URI", "mongodb+srv://cluster0.example.mongodb.net/")
MONGO_ATLAS_USERNAME = os.getenv("MONGO_ATLAS_USERNAME", "atlasuser")
MONGO_ATLAS_PASSWORD = os.getenv("MONGO_ATLAS_PASSWORD", "atlaspassword")

# Local MongoDB Connection (Development/testing database)
MONGO_LOCAL_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
MONGO_LOCAL_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_LOCAL_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")

# Vector Search Configuration
DEFAULT_VECTOR_DIMENSIONS = 512  # Default vector dimensions, adjust based on your embedding model
VECTOR_SEARCH_INDEX_NAME = "vector_search_index"

# Search defaults
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_TEXT_SCORE_FIELD = "score"

# Index Settings
TEXT_INDEX_OPTIONS = {
    "weights": {
        "text": 10,
        "label": 5,
        "content_layer": 2
    },
    "name": "text_search_index"
}

def get_mongo_client(use_atlas: Optional[bool] = None) -> Tuple[pymongo.MongoClient, bool]:
    """
    Get MongoDB client based on configuration.
    
    Args:
        use_atlas: Override to force using Atlas (True) or local (False).
                  If None, uses the MONGO_ATLAS_ENABLED environment variable.
    
    Returns:
        Tuple of (MongoDB client, is_atlas_client)
    """
    # Determine whether to use Atlas
    should_use_atlas = use_atlas if use_atlas is not None else MONGO_ATLAS_ENABLED
    
    if should_use_atlas:
        # Connect to MongoDB Atlas
        client = pymongo.MongoClient(
            MONGO_ATLAS_CONNECTION_STRING,
            username=MONGO_ATLAS_USERNAME,
            password=MONGO_ATLAS_PASSWORD
        )
        return client, True
    else:
        # Connect to local MongoDB
        client = pymongo.MongoClient(
            MONGO_LOCAL_SERVER,
            username=MONGO_LOCAL_USERNAME,
            password=MONGO_LOCAL_PASSWORD
        )
        return client, False

# MongoDB collection naming conventions
def get_collection_name(kb_name: str, file_name: str, content_type: str) -> str:
    """Generate a standardized collection name for MongoDB"""
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{kb_name}_{file_name}_{content_type}_{ts}"

def get_db_collection(db_name: str, collection_name: str, use_atlas: Optional[bool] = None) -> Tuple[pymongo.collection.Collection, bool]:
    """
    Get a MongoDB collection from either Atlas or local MongoDB.
    
    Args:
        db_name: Database name
        collection_name: Collection name
        use_atlas: Override to force using Atlas (True) or local (False)
    
    Returns:
        Tuple of (MongoDB collection, is_atlas_collection)
    """
    client, is_atlas = get_mongo_client(use_atlas)
    db = client[db_name]
    collection = db[collection_name]
    return collection, is_atlas
