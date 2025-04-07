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


def convert(file_loc:str) -> dict:
    pipeline_options = PdfPipelineOptions()

    accelerator_options = AcceleratorOptions(
        num_threads=8, device=AcceleratorDevice.AUTO
    )

    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.accelerator_options = accelerator_options

    converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    result = converter.convert(file_loc)
    out = result.document.export_to_dict()
    return out