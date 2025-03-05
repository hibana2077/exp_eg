import json
import logging
import os
import time
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

app = FastAPI()

Path("/root/mortis/inf_db").mkdir(parents=True, exist_ok=True)
Path("/root/mortis/temp").mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting FastAPI server...")
    import uvicorn

    uvicorn.run(app, host=HOST, port=8000, log_level="info")