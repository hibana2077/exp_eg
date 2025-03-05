import json
import logging
import os
import uvicorn
import time
from minio import Minio
from fastapi import FastAPI, HTTPException
from pathlib import Path

import tesserocr
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.tesseract_ocr_model import TesseractOcrOptions
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem


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
def process_file(bk: str, file: str):
    try:
        client = Minio(
            "minio:9000",
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False,
        )
        # Download data of an object.
        client.fget_object(bk, file, "/opt/mortis/temp/" + file)
        time.sleep(5) # simulate long processing time
        # remove file
        os.remove("/opt/mortis/temp/" + file)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=14514, log_level="info")