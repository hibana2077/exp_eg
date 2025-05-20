import os
import datetime
import logging
import pymongo
from typing import List, Dict, Any, Optional, Union, Tuple

# Import both implementations
import infinity
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("migration_helper")

def migrate_kb(kb_name: str):
    """
    Migrate a knowledge base from Infinity to Qdrant
    
    Parameters:
    -----------
    kb_name : str
        Name of the knowledge base to migrate
    """
    # Environment variables
    INFINITY_HOST = os.getenv("INFINITY_HOST", "infinity")
    INFINITY_PORT = int(os.getenv("INFINITY_PORT", "23817"))
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
    MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_PWD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")
    
    logger.info(f"Starting migration for knowledge base: {kb_name}")
    
    # Connect to MongoDB to get file metadata
    mongo_client = pymongo.MongoClient(MONGO_SERVER, username=MONGO_USER, password=MONGO_PWD)
    mongo_db = mongo_client["mortis"]
    mongo_coll = mongo_db["index_info"]
    
    # Get knowledge base info
    kb_info = mongo_coll.find_one({"kb_name": kb_name})
    if not kb_info:
        logger.error(f"Knowledge base {kb_name} not found in MongoDB")
        return False
    
    # Connect to Infinity
    infinity_client = infinity.connect(infinity.NetworkAddress(INFINITY_HOST, INFINITY_PORT))
    try:
        infinity_db = infinity_client.get_database(kb_name.lower())
    except Exception as e:
        logger.error(f"Failed to connect to Infinity database {kb_name.lower()}: {e}")
        return False
    
    # Connect to Qdrant
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Get all tables in Infinity database for this KB
    tables = kb_info.get("files", [])
    if not tables:
        logger.warning(f"No files found for knowledge base {kb_name}")
        return False
    
    # Process each file's tables
    for file_info in tables:
        # Migrate text table
        texts_table_name = file_info.get("texts_table_name")
        if texts_table_name:
            migrate_table_to_qdrant(
                infinity_db=infinity_db,
                qdrant_client=qdrant_client,
                table_name=texts_table_name,
                vector_field="embedding",
                dimension=1024
            )
        
        # Migrate images table
        images_table_name = file_info.get("images_table_name")
        if images_table_name:
            migrate_table_to_qdrant(
                infinity_db=infinity_db,
                qdrant_client=qdrant_client,
                table_name=images_table_name,
                vector_field="embedding",
                dimension=512  # CLIP embedding dimension
            )
        
        # Migrate tables table
        tables_table_name = file_info.get("tables_table_name")
        if tables_table_name:
            migrate_table_to_qdrant(
                infinity_db=infinity_db,
                qdrant_client=qdrant_client,
                table_name=tables_table_name,
                vector_field="embedding",
                dimension=1024
            )
    
    # Disconnect from Infinity
    infinity_client.disconnect()
    logger.info(f"Migration completed for knowledge base: {kb_name}")
    return True

def migrate_table_to_qdrant(
    infinity_db,
    qdrant_client: QdrantClient,
    table_name: str,
    vector_field: str = "embedding",
    dimension: int = 1024
):
    """
    Migrate a table from Infinity to a Qdrant collection
    
    Parameters:
    -----------
    infinity_db : infinity.Database
        Infinity database object
    qdrant_client : QdrantClient
        Qdrant client instance
    table_name : str
        Name of the table/collection
    vector_field : str
        Name of the vector field in the Infinity table
    dimension : int
        Dimension of the vectors
    """
    logger.info(f"Migrating table {table_name} to Qdrant")
    
    # Get table from Infinity
    try:
        table = infinity_db.get_table(table_name)
    except Exception as e:
        logger.error(f"Failed to get table {table_name} from Infinity: {e}")
        return False
    
    # Get all data from Infinity table
    try:
        data = table.output(["*"]).to_pl()[0]
        logger.info(f"Retrieved {len(data)} records from Infinity table {table_name}")
    except Exception as e:
        logger.error(f"Failed to retrieve data from table {table_name}: {e}")
        return False
    
    # Create collection in Qdrant if it doesn't exist
    try:
        try:
            qdrant_client.get_collection(collection_name=table_name)
            logger.info(f"Collection {table_name} already exists in Qdrant")
        except Exception:
            # Collection doesn't exist, create it
            qdrant_client.create_collection(
                collection_name=table_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection {table_name}")
    except Exception as e:
        logger.error(f"Failed to create Qdrant collection {table_name}: {e}")
        return False
    
    # Convert data to Qdrant points and insert
    try:
        points = []
        for i, row in enumerate(data.iter_rows(named=True)):
            # Convert row to dictionary and extract vector
            row_dict = {k: v for k, v in row.items() if k != vector_field}
            vector = row.get(vector_field)
            
            # Create Qdrant point
            if vector is not None:
                points.append(PointStruct(
                    id=i,
                    vector=vector.tolist() if hasattr(vector, 'tolist') else vector,
                    payload=row_dict
                ))
        
        # Insert points in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            qdrant_client.upsert(
                collection_name=table_name,
                points=batch
            )
            logger.info(f"Inserted batch {i//batch_size + 1} of {(len(points)-1)//batch_size + 1} for {table_name}")
        
        logger.info(f"Migration completed for table {table_name}, inserted {len(points)} records")
        return True
    except Exception as e:
        logger.error(f"Failed to insert data into Qdrant collection {table_name}: {e}")
        return False

def migrate_all_kbs():
    """
    Migrate all knowledge bases from Infinity to Qdrant
    """
    # Connect to MongoDB to get all knowledge bases
    MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
    MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_PWD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")
    
    mongo_client = pymongo.MongoClient(MONGO_SERVER, username=MONGO_USER, password=MONGO_PWD)
    mongo_db = mongo_client["mortis"]
    mongo_coll = mongo_db["index_info"]
    
    # Get all knowledge bases
    kbs = mongo_coll.find({})
    
    # Migrate each knowledge base
    success_count = 0
    fail_count = 0
    for kb in kbs:
        kb_name = kb.get("kb_name")
        if kb_name:
            result = migrate_kb(kb_name)
            if result:
                success_count += 1
            else:
                fail_count += 1
    
    logger.info(f"Migration completed for all knowledge bases. Success: {success_count}, Failed: {fail_count}")
    return success_count, fail_count

if __name__ == "__main__":
    # If run directly, migrate all knowledge bases
    migrate_all_kbs()
