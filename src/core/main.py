import json
import logging
import os
import uvicorn
import time
import pymongo
from minio import Minio
from fastapi import FastAPI, HTTPException
from pathlib import Path

from utils.parse import convert
from utils.vec_store import save_vec_store

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
            file_name = "/root/mortis/temp/" + file_name
            logging.info(f"Processing file: {file_name}")
            data = convert(file_name)
            # Save the vector store
            status = save_vec_store(kb_name, file_name, data)
            # Save the index information
            index_info["files"].append({
                "file_name": file_name,
                "status": status['status'],
                "texts_table_name": status['texts_table_name'],
                # "pictures_table_name": status['pictures_table_name'],
            })
            # Remove file
            os.remove(file_name)
        # Write index infomation to MongoDB
        mongo_collection.update_one(
            {"kb_name": kb_name},
            {"$set": index_info},
            upsert=True
        )
        return {"status": "success", "message": "File processed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)+" "+str(e.__traceback__.tb_lineno)}

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=14514, log_level="info")