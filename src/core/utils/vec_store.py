import os
import datetime
import base64
import io
import pprint
import json
import logging
from tempfile import NamedTemporaryFile
import pymongo
from typing import Dict, Any, Optional, List
from transformers import AutoTokenizer
from docling.chunking import HybridChunker  # type: ignore
from fastembed import TextEmbedding, ImageEmbedding  # type: ignore
from cfg.emb_settings import EMB_MODEL, IMG_EMB_MODEL, TABLE_EMB_MODEL, TABLE_CHUNK_MAX_TOKENS
from cfg.table_format import TEXT_FORMAT, IMAGE_FORMAT, TABLE_FORMAT
from .parse import table_convert, merge_adjacent_tables
from .mongo_atlas_config import get_db_collection, get_mongo_client, MONGO_ATLAS_ENABLED


class VecStore:
    def __init__(self, kb_name: str, use_atlas: Optional[bool] = None):
        """
        Initialize the VecStore.
        
        Args:
            kb_name: Knowledge base name
            use_atlas: If True, use MongoDB Atlas; if False, use local MongoDB;
                      if None, use MONGO_ATLAS_ENABLED environment variable
        """
        self.kb_name = kb_name.lower()
        self.use_atlas = use_atlas
        self._connect_db()
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.texts_table_name = f"file_{ts}_texts"
        self.images_table_name = f"file_{ts}_images"
        self.tables_table_name = f"file_{ts}_tables"
        self.text_model = TextEmbedding(model_name=EMB_MODEL)
        self.image_model = ImageEmbedding(model_name=IMG_EMB_MODEL)
        self.table_model = TextEmbedding(model_name=TABLE_EMB_MODEL)
        self.tokenizer = AutoTokenizer.from_pretrained(TABLE_EMB_MODEL)
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=TABLE_CHUNK_MAX_TOKENS,
            merge_peers=True,
        )

    def _connect_db(self):
        """Connect to MongoDB (either Atlas or local)"""
        self.mongo_client, self.is_atlas = get_mongo_client(self.use_atlas)
        self.db = self.mongo_client[self.kb_name]
        db_name_src = "Atlas" if self.is_atlas else "Local"
        print(f"Connected to {db_name_src} MongoDB: {self.kb_name}")

    def _disconnect(self):
        """Disconnect from MongoDB"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()

    def _common_transform(self, data: dict) -> dict:
        prov = data.get("prov", [{}])[0]
        row = {
            "self_ref": data.get("self_ref"),
            "parent": data.get("parent", {}).get("$ref"),
            "content_layer": data.get("content_layer"),
            "label": data.get("label"),
            "page": prov.get("page_no"),
            "coord": list(prov.get("bbox", {}).values())[:4],
            "coord_origin": prov.get("bbox", {}).get("coord_origin"),
        }
        return row

    def text_transform(self, data: dict) -> dict:
        row = self._common_transform(data)
        txt = data.get("text", "")
        row.update({
            "text": txt, #add flattened text
            "orig": data.get("orig"),
        })
        return row

    def image_transform(self, data: dict) -> dict:
        row = self._common_transform(data)
        image_info = data.get("image", {})
        uri = image_info.get("uri", "")
        encoded = uri.split(",", 1)[1] if "," in uri else uri
        img_bytes = base64.b64decode(encoded)
        with NamedTemporaryFile(suffix='.png') as tmp:
            tmp.write(img_bytes)
            tmp.flush()
            emb = list(self.image_model.embed([tmp.name]))[0].tolist()
        row.update({
            "image": encoded,
            "dpi": image_info.get("dpi"),
            "size": list(image_info.get("size", {}).values()),
            "type": image_info.get("mimetype"),
            "embedding": emb,
        })
        return row

    def table_transform(self, chunk) -> dict:
        txt = chunk.text
        return {"text": txt, "embedding": list(self.table_model.embed([txt]))[0].tolist()}

    def save(self, file_name: str, data: dict, meta_data) -> dict:
        status = {
            "status": "success",
            "texts_table_name": self.texts_table_name,
            "images_table_name": self.images_table_name,
            "tables_table_name": self.tables_table_name,
        }
        
        # Texts
        ## batch-embed
        pure_texts = [t.get("text", "") for t in data.get("texts", [])]
        embeds = list(self.text_model.embed(pure_texts))
        logging.info(f"Type of embeds[0]: {type(embeds[0])}")
        texts = [self.text_transform(t) for t in data.get("texts", [])]
        for i, text in enumerate(texts):
            text['embedding'] = embeds[i].tolist()
        
        # Create MongoDB collection for texts
        if texts:
            # Create text indexes for search capabilities
            self.db[self.texts_table_name].create_index([("text", pymongo.TEXT)])
            
            # Create vector search index (note: this would typically be done through Atlas UI)
            # This is a placeholder to indicate where you would configure the vector search index
            
            # Insert the texts into MongoDB
            self.db[self.texts_table_name].insert_many(texts)
        
        # Images
        pics = [self.image_transform(i) for i in data.get("pictures", [])]
        if pics:
            # Create MongoDB collection for images and insert data
            self.db[self.images_table_name].insert_many(pics)
        else:
            status["images_table_name"] = ""
        
        # Tables
        tables = []
        if getattr(meta_data.document, "tables", None):
            all_tabs = merge_adjacent_tables(meta_data)
            md = "\n\n\n".join(tbl.to_markdown(index=False) for tbl in all_tabs)
            # write to md file
            with NamedTemporaryFile(suffix='.md', delete=False) as tmp:
                tmp.write(md.encode())
                tmp.flush()
                # Convert to pure doc
            pure_doc = table_convert(tmp.name)
            chunks = list(self.chunker.chunk(dl_doc=pure_doc))
            tables = [self.table_transform(c) for c in chunks]
            # Remove the temporary file
            os.remove(tmp.name)
            if tables:
                # Create MongoDB collection for tables and insert data
                self.db[self.tables_table_name].insert_many(tables)
        else:
            status["tables_table_name"] = ""
            
        # Record the collection creation in a metadata collection
        metadata_collection = self.db["metadata"]
        metadata_collection.insert_one({
            "file_name": file_name,
            "texts_table_name": self.texts_table_name if texts else "",
            "images_table_name": self.images_table_name if pics else "",
            "tables_table_name": self.tables_table_name if tables else "",
            "created_at": datetime.datetime.now()
        })
        
        self._disconnect()
        return status

    @staticmethod
    def list_all_tables(kb_name: str, use_atlas: Optional[bool] = None):
        """
        List all tables/collections in a knowledge base.
        
        Args:
            kb_name: Knowledge base name
            use_atlas: If True, use MongoDB Atlas; if False, use local MongoDB;
                      if None, use MONGO_ATLAS_ENABLED environment variable
                      
        Returns:
            List of collection names
        """
        # Get MongoDB client
        client, is_atlas = get_mongo_client(use_atlas)
        
        # Get database
        db = client[kb_name.lower()]
        
        # Get collection names (tables)
        tables = db.list_collection_names()
        
        # Close connection
        client.close()
        
        db_name_src = "Atlas" if is_atlas else "Local"
        print(f"Listed tables from {db_name_src} MongoDB: {len(tables)} tables found")
        
        return tables

    @staticmethod
    def list_all_tables_mongo(kb_name: str, use_atlas: Optional[bool] = None):
        """
        Get metadata about tables in a knowledge base from MongoDB.
        
        Args:
            kb_name: Knowledge base name
            use_atlas: If True, use MongoDB Atlas; if False, use local MongoDB; 
                      if None, use MONGO_ATLAS_ENABLED environment variable
                      
        Returns:
            Dictionary with knowledge base metadata
        """
        # Get MongoDB client
        client, is_atlas = get_mongo_client(use_atlas)
        
        # Access the mortis database (metadata database)
        db = client["mortis"]
        coll = db.get_collection("index_info")
        
        # Find the knowledge base metadata
        result = coll.find_one({"kb_name": kb_name}, {"_id": 0})
        
        # Close connection
        client.close()
        
        return result

# Backward compatibility functions

def save_vec_store(kb_name: str, file_name: str, data: dict, meta_data, use_atlas: Optional[bool] = None) -> dict:
    """Save data to vector store (MongoDB)"""
    return VecStore(kb_name, use_atlas).save(file_name, data, meta_data)


def list_all_tables(kb_name: str, use_atlas: Optional[bool] = None):
    """List all tables/collections in a knowledge base"""
    return VecStore.list_all_tables(kb_name, use_atlas)


def list_all_tables_mongo(kb_name: str, use_atlas: Optional[bool] = None):
    """Get metadata about tables in a knowledge base"""
    return VecStore.list_all_tables_mongo(kb_name, use_atlas)