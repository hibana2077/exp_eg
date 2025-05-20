import json
import logging
import os
import pprint
import uvicorn
import time
import pymongo

import pandas as pd
import numpy as np
import polars as pl

from minio import Minio
from fastembed import TextEmbedding
from fastapi import FastAPI, HTTPException
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from utils.embedding import add_emb_cond
# Import both Infinity and Qdrant implementations
from utils.indexing import indexing, add_index_into_condiction
from utils.qdrant_indexing import qdrant_indexing, add_qdrant_index_into_condition 
from utils.search import search as infinity_search
from utils.qdrant_search import qdrant_search
from utils.parse import convert
# Import both vector store implementations
from utils.vec_store import save_vec_store as infinity_save_vec_store
from utils.vec_store import list_all_tables, list_all_tables_mongo
from utils.qdrant_store import save_vec_store as qdrant_save_vec_store
from utils.qdrant_store import list_all_tables as qdrant_list_all_tables
from utils.qdrant_store import list_all_tables_mongo as qdrant_list_all_tables_mongo

from cfg.emb_settings import IMG_CLIP_EMB_MODEL, IMG_EMB_SEARCH_METRIC

# Set to True to use Qdrant, False to use Infinity
USE_QDRANT = True

HOST = os.getenv("HOST", "127.0.0.1")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")
MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")

# MongoDB Database Setup
mongo_client = pymongo.MongoClient(
    MONGO_SERVER,
    username=MONGO_INITDB_ROOT_USERNAME,
    password=MONGO_INITDB_ROOT_PASSWORD
)
mongo_db = mongo_client["mortis"]
mongo_collection = mongo_db["index_info"]

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logging.info("Starting FastAPI server...")

Path("/root/mortis/temp").mkdir(parents=True, exist_ok=True)

# Select the appropriate functions based on the selected backend
if USE_QDRANT:
    # Use Qdrant implementations
    search_func = qdrant_search
    save_vec_store_func = qdrant_save_vec_store
    list_all_tables_func = qdrant_list_all_tables
    list_all_tables_mongo_func = qdrant_list_all_tables_mongo
    indexing_func = qdrant_indexing
    add_index_into_condition_func = add_qdrant_index_into_condition
else:
    # Use Infinity implementations
    search_func = infinity_search
    save_vec_store_func = infinity_save_vec_store
    list_all_tables_func = list_all_tables
    list_all_tables_mongo_func = list_all_tables_mongo
    indexing_func = indexing
    add_index_into_condition_func = add_index_into_condiction

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    try:
        # Check MongoDB connection
        mongo_client.admin.command('ping')
        # Check Minio connection
        client = Minio(
            "minio:9000",
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False,
        )
        client.list_buckets()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/minio_connect_test")
def minio_connect_test():
    try:
        client = Minio(
            "minio:9000",
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False,
        )
        client.list_buckets()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process_file")
async def process_file(task_queue:dict):
    """
    Process a file in the knowledge base.
    
    Parameters:
    -----------
    task_queue : dict
        Dictionary containing the task details.
        {
            "kb_name": "knowledge_base_name",
            "file_name": "file_name.pdf"
        }
    
    Returns:
    --------
    Dict[str, Any]
        Status of the file processing.
    """
    kb_name = task_queue["kb_name"]
    file_name = task_queue["file_name"]
    
    try:
        client = Minio(
            "minio:9000",
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False,
        )
        
        # Check if the file already exists
        kb_info = mongo_collection.find_one({"kb_name": kb_name})
        if not kb_info:
            # Create index entry for new knowledge base
            kb_info = {
                "kb_name": kb_name,
                "files": []
            }
            mongo_collection.insert_one(kb_info)
        
        # Get the updated index info
        index_info = mongo_collection.find_one({"kb_name": kb_name})
        
        # Check if this file is already processed
        if index_info and "files" in index_info:
            if len(index_info["files"]) != 0:
                for file in index_info["files"]:
                    if file["file_name"] == file_name:
                        continue # If the file already exists, skip it
            
            # Download the file from Minio
            client.fget_object(kb_name.lower(), file_name, "/root/mortis/temp/" + file_name)
            
            # Process the file
            logging.info(f"Processing file: {file_name}")
            data, meta_data = convert("/root/mortis/temp/" + file_name)
            
            # Save to vector store using the appropriate function
            status = save_vec_store_func(kb_name, file_name, data, meta_data)
            
            logging.info(f"status: {status}, texts_table_name: {status['texts_table_name']}, images_table_name: {status['images_table_name']}")
            
            # Save the index information to MongoDB
            index_info["files"].append({
                "file_name": file_name,
                "status": status['status'],
                "texts_table_name": status['texts_table_name'],
                "images_table_name": status['images_table_name'],
                "tables_table_name": status.get('tables_table_name', "")
            })
            
            mongo_collection.update_one(
                {"kb_name": kb_name},
                {"$set": {"files": index_info["files"]}}
            )
        
        return {"status": "success", "message": "File processed successfully"}
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/list_tables/{kb_name}")
async def list_tables(kb_name: str):
    """
    List all tables/collections in a knowledge base.
    
    Parameters:
    -----------
    kb_name : str
        Name of the knowledge base.
        
    Returns:
    --------
    Dict[str, Any]
        List of tables/collections in the knowledge base.
    """
    try:
        # Get the list of tables/collections using the appropriate function
        tables = list_all_tables_func(kb_name)
        mongo_result = list_all_tables_mongo_func(kb_name)
        
        return {"status": "success", "tables": tables, "mongo_result": mongo_result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/search")
async def search(data: dict):
    """
    Search in the knowledge base.
    
    Parameters:
    -----------
    data : dict
        Dictionary containing the search parameters.
        {
            "kb_name": "knowledge_base_name",
            "tables": [
                ["texts_table_name", "images_table_name", "tables_table_name"],
                ...
            ],
            "select_cols": ["*"],
            "conditions": {
                "text": [
                    {"field": "text", "query": "query_text", 'topn': 10}
                ]
            },
            "do_image_search": true,
            "limit": 10,
            "return_format": "pd"
        }
        
    Returns:
    --------
    Dict[str, Any]
        Search results.
    """
    pprint.pprint(data)
    try:
        return_tables = []
        for table in data["tables"]:
            # Text data search
            index_name = indexing_func(
                db_name=data["kb_name"],
                table_name=table[0]
            )
            
            update_condition = add_index_into_condition_func(
                data["conditions"],
                index_name
            )
            
            update_condition = add_emb_cond(update_condition)
            
            # Perform search using the appropriate function
            result = search_func(
                db_name=data["kb_name"],
                collection_name=table[0],
                select_cols=data["select_cols"],
                conditions=update_condition,
                limit=data["limit"],
                return_format=data["return_format"]
            )
            
            result = result[0]
            pprint.pprint(result)
            
            # Convert result to the requested format
            if data["return_format"] == "pl":  # type -> pl.DataFrame
                result = result.to_dict(as_series=False)
            elif data["return_format"] == "pd":  # type -> pd.DataFrame
                result = result.to_dict()
            elif data["return_format"] == "arrow":  # type -> pyarrow.Table
                result = result.to_pydict()
            elif data["return_format"] == "raw":
                result = result
            else:
                raise ValueError("Invalid return format")
                
            # Add the result to the return_tables
            return_tables.append({
                "table_name": table[0],
                "result": result
            })
            
            # Table data search
            if table[2] != "":
                return_tables.append({
                    "table_name": table[2],
                    "result": result
                })
                
                index_name = indexing_func(
                    db_name=data["kb_name"],
                    table_name=table[2]
                )
                
                update_condition = add_index_into_condition_func(
                    data["conditions"],
                    index_name
                )
                
                update_condition = add_emb_cond(update_condition)
                
                # Perform search using the appropriate function
                result = search_func(
                    db_name=data["kb_name"],
                    collection_name=table[2],
                    select_cols=data["select_cols"],
                    conditions=update_condition,
                    limit=data["limit"],
                    return_format=data["return_format"]
                )
                
                result = result[0]
                
                # Convert result to the requested format
                if data["return_format"] == "pl":  # type -> pl.DataFrame
                    result = result.to_dict(as_series=False)
                elif data["return_format"] == "pd":  # type -> pd.DataFrame
                    result = result.to_dict()
                elif data["return_format"] == "arrow":  # type -> pyarrow.Table
                    result = result.to_pydict()
                elif data["return_format"] == "raw":
                    result = result
                else:
                    raise ValueError("Invalid return format")
                    
                return_tables.append({
                    "table_name": table[2],
                    "result": result
                })
                
            # Image search
            if data["do_image_search"]:
                print("Image search")
                clip_text_model = TextEmbedding(IMG_CLIP_EMB_MODEL)
                
                # Perform image search using the appropriate function
                image_result = search_func(
                    db_name=data["kb_name"],
                    collection_name=table[1],
                    select_cols=["image"],
                    conditions={
                        "dense": [
                            {
                                "field": "embedding",
                                "query": list(clip_text_model.embed(data["conditions"]["text"][0]['query']))[0],
                                "element_type": "float",
                                "metric": IMG_EMB_SEARCH_METRIC,
                                "topn": data["limit"]
                            }
                        ]
                    },
                    limit=data["limit"],
                    return_format=data["return_format"]
                )
                
                image_result = image_result[0]
                
                # Convert result to the requested format
                if data["return_format"] == "pl":
                    image_result = image_result.to_dict(as_series=False)
                elif data["return_format"] == "pd":
                    image_result = image_result.to_dict()
                elif data["return_format"] == "arrow":
                    image_result = image_result.to_pydict()
                elif data["return_format"] == "raw":
                    image_result = image_result
                else:
                    raise ValueError("Invalid return format")
                    
                return_tables.append({
                    "table_name": table[1],
                    "result": image_result
                })
                
        # Return the tables
        tables = {
            "kb_name": data["kb_name"],
            "tables": return_tables
        }
        
        if tables['tables'] == []:
            pprint.pprint(tables)
            
        return {"status": "success", "tables": tables}
    
    except Exception as e:
        return {"status": "error", "message": str(e) + " " + str(e.__traceback__.tb_lineno)}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=14514, log_level="info")
