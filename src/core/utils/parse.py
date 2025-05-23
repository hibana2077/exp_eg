import json
import logging
import os
import time
import pandas as pd
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

CORES = os.cpu_count()-1 or 1

def convert(file_loc:str) -> dict:
    pipeline_options = PdfPipelineOptions()

    accelerator_options = AcceleratorOptions(
        num_threads=CORES, device=AcceleratorDevice.AUTO
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
    return out, result

def merge_adjacent_tables(meta_data):
    all_tables = []

    # for i in range(len(meta_data.document.tables)):
    for idx, table in enumerate(meta_data.document.tables):
        table_df = table.export_to_dataframe()
        print(f"\nProcessing table {idx}, shape: {table_df.shape}")

        # 檢查是否符合合併條件
        if all_tables and list(table_df.columns.values) == list(range(len(table_df.columns))) and len(all_tables[-1].columns) == len(table_df.columns):
            print(f"  Merging table {idx} with previous table")
            unify_columns = list(all_tables[-1].columns)
            table_df.columns = unify_columns

            table_df = pd.concat([all_tables[-1], table_df], ignore_index=True)
            all_tables.pop()
        else:
            print(f"  Table {idx} added without merging")

        all_tables.append(table_df)

    print(f"\nTotal merged tables: {len(all_tables)}")
    return all_tables

def table_convert(file_loc: str) -> dict:
    return DocumentConverter().convert(source=file_loc).document