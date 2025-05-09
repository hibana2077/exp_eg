"""
MongoDB Migration Utility

This script provides functions to migrate data between local MongoDB and MongoDB Atlas.
It allows users to sync data between development and production environments.
"""

import os
import pymongo
import datetime
import argparse
import logging
from typing import Dict, Any, List, Optional, Tuple

from .mongo_atlas_config import (
    get_mongo_client,
    MONGO_ATLAS_CONNECTION_STRING,
    MONGO_LOCAL_SERVER
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_collection(
    source_client: pymongo.MongoClient,
    target_client: pymongo.MongoClient,
    db_name: str,
    collection_name: str,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Migrate a single collection from source to target MongoDB.
    
    Args:
        source_client: Source MongoDB client
        target_client: Target MongoDB client
        db_name: Database name
        collection_name: Collection name
        overwrite: Whether to overwrite existing documents
        
    Returns:
        Migration statistics
    """
    # Get source and target collection
    source_db = source_client[db_name]
    source_collection = source_db[collection_name]
    
    target_db = target_client[db_name]
    target_collection = target_db[collection_name]
    
    # Check if target collection exists and whether to overwrite
    if collection_name in target_db.list_collection_names() and not overwrite:
        logger.warning(f"Target collection {db_name}.{collection_name} already exists. Skip.")
        return {
            "status": "skipped",
            "collection": collection_name,
            "reason": "target_exists_and_no_overwrite"
        }
    
    # Count documents in source collection
    source_count = source_collection.count_documents({})
    logger.info(f"Migrating {source_count} documents from {db_name}.{collection_name}")
    
    # Retrieve all documents from source collection
    cursor = source_collection.find({})
    documents = list(cursor)
    
    if not documents:
        logger.warning(f"No documents found in source collection {db_name}.{collection_name}")
        return {
            "status": "empty",
            "collection": collection_name
        }
    
    # Drop existing collection if overwrite is True
    if collection_name in target_db.list_collection_names() and overwrite:
        target_collection.drop()
    
    # Insert documents into target collection
    if len(documents) > 0:
        target_collection.insert_many(documents)
    
    # Create indexes on target collection (if they exist in source)
    index_info = source_collection.index_information()
    for index_name, index_info in index_info.items():
        if index_name != '_id_':  # Skip default _id index
            keys = index_info['key']
            options = {k: v for k, v in index_info.items() 
                     if k not in ['ns', 'v', 'key']}
            if 'background' in options:
                options.pop('background', None)  # Not needed for Atlas
            
            target_collection.create_index(keys, **options)
    
    # Verify migration
    target_count = target_collection.count_documents({})
    
    return {
        "status": "success" if target_count == source_count else "partial",
        "collection": collection_name,
        "source_documents": source_count,
        "migrated_documents": target_count
    }

def migrate_database(
    source_client: pymongo.MongoClient,
    target_client: pymongo.MongoClient,
    db_name: str,
    include_collections: Optional[List[str]] = None,
    exclude_collections: Optional[List[str]] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Migrate a database from source to target MongoDB.
    
    Args:
        source_client: Source MongoDB client
        target_client: Target MongoDB client
        db_name: Database name to migrate
        include_collections: List of collections to include (if None, all collections)
        exclude_collections: List of collections to exclude
        overwrite: Whether to overwrite existing collections
        
    Returns:
        Migration statistics
    """
    source_db = source_client[db_name]
    
    # Get list of collections to migrate
    all_collections = source_db.list_collection_names()
    
    if include_collections:
        collections = [c for c in all_collections if c in include_collections]
    else:
        collections = all_collections
    
    if exclude_collections:
        collections = [c for c in collections if c not in exclude_collections]
    
    logger.info(f"Migrating {len(collections)} collections from {db_name}")
    
    results = []
    for collection in collections:
        result = migrate_collection(
            source_client,
            target_client,
            db_name,
            collection,
            overwrite
        )
        results.append(result)
    
    return {
        "database": db_name,
        "total_collections": len(collections),
        "successful_migrations": len([r for r in results if r["status"] == "success"]),
        "skipped_migrations": len([r for r in results if r["status"] == "skipped"]),
        "empty_collections": len([r for r in results if r["status"] == "empty"]),
        "partial_migrations": len([r for r in results if r["status"] == "partial"]),
        "details": results
    }

def migrate_to_atlas(
    db_names: List[str],
    include_collections: Optional[List[str]] = None,
    exclude_collections: Optional[List[str]] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Migrate from local MongoDB to MongoDB Atlas.
    
    Args:
        db_names: List of database names to migrate
        include_collections: List of collections to include
        exclude_collections: List of collections to exclude
        overwrite: Whether to overwrite existing collections
        
    Returns:
        Migration statistics
    """
    logger.info(f"Starting migration from Local MongoDB to MongoDB Atlas")
    logger.info(f"Source: {MONGO_LOCAL_SERVER}")
    logger.info(f"Target: {MONGO_ATLAS_CONNECTION_STRING}")
    
    # Get MongoDB clients
    local_client, _ = get_mongo_client(use_atlas=False)
    atlas_client, _ = get_mongo_client(use_atlas=True)
    
    results = []
    for db_name in db_names:
        result = migrate_database(
            local_client,
            atlas_client,
            db_name,
            include_collections,
            exclude_collections,
            overwrite
        )
        results.append(result)
    
    local_client.close()
    atlas_client.close()
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "direction": "local_to_atlas",
        "databases_migrated": len(results),
        "details": results
    }

def migrate_from_atlas(
    db_names: List[str],
    include_collections: Optional[List[str]] = None,
    exclude_collections: Optional[List[str]] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Migrate from MongoDB Atlas to local MongoDB.
    
    Args:
        db_names: List of database names to migrate
        include_collections: List of collections to include
        exclude_collections: List of collections to exclude
        overwrite: Whether to overwrite existing collections
        
    Returns:
        Migration statistics
    """
    logger.info(f"Starting migration from MongoDB Atlas to Local MongoDB")
    logger.info(f"Source: {MONGO_ATLAS_CONNECTION_STRING}")
    logger.info(f"Target: {MONGO_LOCAL_SERVER}")
    
    # Get MongoDB clients
    atlas_client, _ = get_mongo_client(use_atlas=True)
    local_client, _ = get_mongo_client(use_atlas=False)
    
    results = []
    for db_name in db_names:
        result = migrate_database(
            atlas_client,
            local_client,
            db_name,
            include_collections,
            exclude_collections,
            overwrite
        )
        results.append(result)
    
    local_client.close()
    atlas_client.close()
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "direction": "atlas_to_local",
        "databases_migrated": len(results),
        "details": results
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MongoDB Migration Utility")
    parser.add_argument("direction", choices=["to_atlas", "from_atlas"], 
                        help="Migration direction")
    parser.add_argument("--databases", required=True, nargs="+", 
                        help="Database names to migrate")
    parser.add_argument("--include", nargs="+", help="Collections to include")
    parser.add_argument("--exclude", nargs="+", help="Collections to exclude")
    parser.add_argument("--overwrite", action="store_true", 
                        help="Overwrite existing collections")
    
    args = parser.parse_args()
    
    if args.direction == "to_atlas":
        result = migrate_to_atlas(
            args.databases,
            args.include,
            args.exclude,
            args.overwrite
        )
    else:
        result = migrate_from_atlas(
            args.databases,
            args.include,
            args.exclude,
            args.overwrite
        )
    
    logger.info(f"Migration completed: {result['databases_migrated']} databases processed")
    for db_result in result["details"]:
        logger.info(f"Database {db_result['database']}: "
                   f"{db_result['successful_migrations']} successful, "
                   f"{db_result['skipped_migrations']} skipped, "
                   f"{db_result['empty_collections']} empty, "
                   f"{db_result['partial_migrations']} partial")
