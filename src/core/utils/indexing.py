import datetime
import os
import pymongo
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from pymongo.operations import SearchIndexModel
from cfg.emb_settings import EMB_DIM
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
    
    # Create indexes for vector search (assuming 'embedding' field exists)
    try:
        search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": EMB_DIM,  # 根據您的嵌入向量維度設定
                        "path": "embedding",    # 向量欄位名稱
                        "similarity": "dotProduct"  # 相似度計算方法，可選擇 'euclidean', 'cosine', 'dotProduct'
                    }
                ]
            },
            name=index_name,  # 索引名稱
            type="vectorSearch"
        )

        stats = collection.create_search_index(model=search_index_model)
        print(f"MongoDB index creation completed: {index_name}, stats: {stats}")
        return search_index_model
    except Exception as e:
        print(f"Warning: Vector index creation may require MongoDB Atlas UI configuration: {e}")

def add_index_into_condiction(condiction, index_name:str):
    # In MongoDB, we don't need to specify index name for queries
    # But we'll keep this function for compatibility with existing code
    text_condictions = condiction.get("text", [])
    for cond in text_condictions:
        cond['options'] = {'index_name': index_name}
    return condiction