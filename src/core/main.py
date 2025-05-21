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

# Import Qdrant implementations
from utils.embedding import add_emb_cond
from utils.qdrant_indexing import qdrant_indexing, add_qdrant_index_into_condition 
from utils.qdrant_search import qdrant_search
from utils.parse import convert
from utils.qdrant_store import save_vec_store as save_vec_store_func
from utils.qdrant_store import list_all_tables as list_all_tables_func
from utils.qdrant_store import list_all_tables_mongo as list_all_tables_mongo_func

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

# Define function aliases
search_func = qdrant_search
indexing_func = qdrant_indexing
add_index_into_condition_func = add_qdrant_index_into_condition

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
    payload:
    {
        "kb_name": "knowledge_base_name",
        "task_queue": [
            {
                "kb_name": "knowledge_base_name",
                "file_name": "file_name"
            },
            ...
        ]
    }
    """
    try:
        client = Minio(
            "minio:9000",
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False,
        )
        # find the kb_name in MongoDB
        kb_name = task_queue["kb_name"]
        index_info = mongo_collection.find_one({"kb_name": kb_name})
        if index_info is None:
            index_info = {
                "kb_name": kb_name,
                "files": [],
            }
            mongo_collection.insert_one(index_info)
        else:
            index_info = {
                "kb_name": kb_name,
                "files": index_info["files"],
            }
        for task in task_queue["task_queue"]:
            kb_name:str = task["kb_name"]
            file_name = task["file_name"]
            if len(index_info["files"]) != 0:
                for file in index_info["files"]:
                    if file["file_name"] == file_name:continue # If the file already exists, skip it
            client.fget_object(kb_name.lower(), file_name, "/root/mortis/temp/" + file_name)
            # Process the file
            # Convert the file to dict
            logging.info(f"Processing file: {file_name}")
            data, meta_data = convert("/root/mortis/temp/" + file_name)
            # Save the vector store
            logging.info(f"Converting Complete, saving to vector store...")
            status = save_vec_store_func(kb_name, file_name, data, meta_data)
            logging.info(f"status: {status}, texts_table_name: {status['texts_table_name']}, images_table_name: {status['images_table_name']}")
            # Save the index information
            index_info["files"].append({
                "file_name": file_name,
                "status": status['status'],
                "texts_table_name": status['texts_table_name'],
                "images_table_name": status['images_table_name'],
                "tables_table_name": status['tables_table_name'],
            })
            # Remove file
            os.remove("/root/mortis/temp/" + file_name)
        # Write index infomation to MongoDB
        mongo_collection.update_one(
            {"kb_name": kb_name},
            {"$set": index_info},
            upsert=True
        )
        return {"status": "success", "message": "File processed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)+" "+str(e.__traceback__.tb_lineno)}

@app.get("/list_tables/{kb_name}")
async def list_tables(kb_name:str):
    """
    payload:
    {
        "kb_name": "knowledge_base_name"
    }
    """
    try:
        # tables = list_all_tables(kb_name)
        tables = list_all_tables_mongo_func(kb_name)
        return {"status": "success", "tables": tables}
    except Exception as e:
        return {"status": "error", "message": str(e)+" "+str(e.__traceback__.tb_lineno)}

@app.post("/search")
async def search(data:dict):
    """
    kb_name: str,
    tables: List[str],
    select_cols: List[str],
    conditions: Dict[str, Any] = None,
    do_image_search: bool = False,
    limit: int = 10,
    return_format: str = "pl"  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)

    Json Example:
    ```python
    {
        "kb_name": "knowledge_base_name",
        "tables": [
            ["texts_table_name", "images_table_name", "tables_table_name"],
            ...
        ],
        "select_cols": ["*"],
        "conditions": { #for all tables
            "text": [
                {"field": "text", "query": "query_text", 'topn': 10}
            ]
        },
        "do_image_search": true,
        "limit": 10,
        "return_format": "pd"
    }
    ```
    """
    pprint.pprint(data)
    try:
        return_tables = []
        for table in data["tables"]:
            # Text data
            index_name = indexing_func(
                db_name=data["kb_name"],
                table_name=table[0]
            )
            update_condition = add_index_into_condition_func(
                data["conditions"],
                index_name
            )
            update_condition = add_emb_cond(update_condition)
            # search
            result = search_func(
                db_name=data["kb_name"],
                table_name=table[0],
                select_cols=data["select_cols"],
                conditions=update_condition,
                limit=data["limit"],
                return_format=data["return_format"]
            )
            result = result[0]
            pprint.pprint(result)
            # all turn to dict
            if data["return_format"] == "pl":# type -> pl.DataFrame
                result = result.to_dict(as_series=False)
            elif data["return_format"] == "pd":# type -> pd.DataFrame
                result = result.to_dict()
            elif data["return_format"] == "arrow":# type -> pyarrow.Table
                result = result.to_pydict()
            elif data["return_format"] == "raw":
                result = result
            else:
                raise ValueError("Invalid return format")
            # add the result to the return_tables
            return_tables.append({
                "table_name": table[0],
                "result": result
            })
            # Table data
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
                # search
                result = search_func(
                    db_name=data["kb_name"],
                    table_name=table[2],
                    select_cols=data["select_cols"],
                    conditions=update_condition,
                    limit=data["limit"],
                    return_format=data["return_format"]
                )
                result = result[0]
                # all turn to dict
                if data["return_format"] == "pl":# type -> pl.DataFrame
                    result = result.to_dict(as_series=False)
                elif data["return_format"] == "pd":# type -> pd.DataFrame
                    result = result.to_dict()
                elif data["return_format"] == "arrow":# type -> pyarrow.Table
                    result = result.to_pydict()
                elif data["return_format"] == "raw":
                    result = result
                else:
                    raise ValueError("Invalid return format")
                return_tables.append({
                    "table_name": table[2],
                    "result": result
                })
            # image data
            if data["do_image_search"]:
                print("Image search")
                clip_text_model = TextEmbedding(IMG_CLIP_EMB_MODEL)
                image_result = search_func(
                    db_name=data["kb_name"],
                    table_name=table[1],
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
                # all turn to dict
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
        return {"status": "error", "message": str(e)+" "+str(e.__traceback__.tb_lineno)}

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=14514, log_level="info")