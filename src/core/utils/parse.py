import json
import logging
import os
import time
from pathlib import Path

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
import tesserocr
