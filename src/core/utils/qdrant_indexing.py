import datetime
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models


def qdrant_indexing(db_name: str, collection_name: str):
    """
    Creates a payload index on the 'text' field of a Qdrant collection.

    This is typically done to optimize text-based searches.

    - **db_name**: Name of the database (for compatibility, not directly used by Qdrant).
    - **collection_name**: The Qdrant collection where the index will be created.
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
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=30,
                lowercase=True
            )
        )
        print(f"Created text index {index_name} on collection {collection_name}")
    except Exception as e:
        # Index might already exist
        print(f"Error creating index (might already exist): {e}")
    
    return index_name


def add_qdrant_index_into_condition(condition: Dict[str, Any], index_name: str) -> Dict[str, Any]:
    """
    Updates search conditions with an index name.

    Note: For Qdrant, this function is a placeholder for compatibility and doesn't
    modify the conditions, as Qdrant doesn't require explicit index naming in search queries.

    - **condition**: The search condition dictionary to potentially update.
    - **index_name**: The name of the index (unused in Qdrant's case).
    """
    # No need to modify conditions for Qdrant
    # Keeping function for compatibility
    return condition
