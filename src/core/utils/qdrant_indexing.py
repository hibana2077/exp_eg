import datetime
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldSchema, PayloadSchemaType, PayloadIndexParams


def qdrant_indexing(db_name: str, collection_name: str):
    """
    Create index for text field in a Qdrant collection.
    
    Parameters:
    -----------
    db_name : str
        Name of the database (not used, kept for compatibility)
    collection_name : str
        Name of the collection to create index for
        
    Returns:
    --------
    index_name : str
        Name of the created index
    """
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Initialize connection
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if collection exists
    try:
        client.get_collection(collection_name=collection_name)
    except Exception as e:
        print(f"Collection {collection_name} does not exist: {e}")
        return None
    
    # Create index name
    index_name = 'text_index_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create text index on the "text" field
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="text",
            field_schema=FieldSchema(
                data_type=PayloadSchemaType.TEXT,
                index_params=PayloadIndexParams(
                    tokenizer="word",
                    min_token_len=2,
                    max_token_len=30,
                    lowercase=True
                )
            )
        )
        print(f"Created text index {index_name} on collection {collection_name}")
    except Exception as e:
        # Index might already exist
        print(f"Error creating index (might already exist): {e}")
    
    return index_name


def add_qdrant_index_into_condition(condition: Dict[str, Any], index_name: str) -> Dict[str, Any]:
    """
    Update search condition with index name.
    For Qdrant, we don't need to specify the index name in the search condition,
    but we keep this function for compatibility.
    
    Parameters:
    -----------
    condition : Dict[str, Any]
        Search condition to update
    index_name : str
        Name of the index to use
        
    Returns:
    --------
    Dict[str, Any]
        Updated search condition
    """
    # No need to modify conditions for Qdrant
    # Keeping function for compatibility
    return condition
