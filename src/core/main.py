import json
import logging
import os
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

from utils.indexing import indexing, add_index_into_condiction
from utils.search import search as search_func
from utils.parse import convert
from utils.vec_store import save_vec_store, list_all_tables, list_all_tables_mongo

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

# EMBEDDING MODEL
EMB_MODEL = "intfloat/multilingual-e5-large"
EMB_DIM = 1024

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logging.info("Starting FastAPI server...")

Path("/root/mortis/temp").mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}

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
            data = convert("/root/mortis/temp/" + file_name)
            # Save the vector store
            status = save_vec_store(kb_name, file_name, data)
            logging.info(f"status: {status}, texts_table_name: {status['texts_table_name']}")
            # Save the index information
            index_info["files"].append({
                "file_name": file_name,
                "status": status['status'],
                "texts_table_name": status['texts_table_name'],
                # "pictures_table_name": status['pictures_table_name'],
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
        tables = list_all_tables_mongo(kb_name)
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
    limit: int = 10,
    return_format: str = "pl"  # Options: "pl" (polars), "pd" (pandas), "arrow" (pyarrow), "raw" (list)
    """
    try:
        return_tables = []
        for table in data["tables"]:
            index_name = indexing(
                db_name=data["kb_name"],
                table_name=table
            )
            update_condiction = add_index_into_condiction(
                data["conditions"],
                index_name
            )
            result = search_func(
                db_name=data["kb_name"],
                table_name=table,
                select_cols=data["select_cols"],
                conditions=update_condiction,
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
                "table_name": table,
                "result": result
            })

        tables = {
            "kb_name": data["kb_name"],
            "tables": return_tables
        }
        return {"status": "success", "tables": tables}
    except Exception as e:
        return {"status": "error", "message": str(e)+" "+str(e.__traceback__.tb_lineno)}

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=14514, log_level="info")