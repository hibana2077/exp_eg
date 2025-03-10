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

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logging.info("Starting FastAPI server...")

Path("/root/mortis/inf_db").mkdir(parents=True, exist_ok=True)
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
        index_info = {
            "kb_name": task_queue["kb_name"],
        }
        for task in task_queue["task_queue"]:
            kb_name = task["kb_name"]
            file_name = task["file_name"]
            client.fget_object(kb_name, file_name, "/root/mortis/temp/" + file_name)
            # Process the file
            # Here you can add your own processing logic
            # Convert the file to dict
            data = convert(file_name)
            # Save the vector store
            save_vec_store(kb_name, file_name, data)
            # Remove file
            os.remove("/root/mortis/temp/" + file_name)
        # Write index infomation to MongoDB
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=14514, log_level="info")