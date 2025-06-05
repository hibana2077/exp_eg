import os
import datetime
import base64
import io
import logging
from tempfile import NamedTemporaryFile
import pymongo
from qdrant_client import QdrantClient
from qdrant_client.http import models
from transformers import AutoTokenizer
from docling.chunking import HybridChunker  # type: ignore
from fastembed import TextEmbedding, ImageEmbedding  # type: ignore
from cfg.emb_settings import EMB_MODEL, IMG_EMB_MODEL, TABLE_EMB_MODEL, TABLE_CHUNK_MAX_TOKENS, TEXT_EMB_DIM, IMG_EMB_DIM, TABLE_EMB_DIM
from cfg.table_format import TEXT_FORMAT, IMAGE_FORMAT, TABLE_FORMAT
from .parse import table_convert, merge_adjacent_tables
from .math_transform import calculate_centroid, get_first_point, one_y_point

logging.basicConfig(level=logging.INFO)

class QdrantVecStore:
    def __init__(self, kb_name: str):
        self.kb_name = kb_name.lower()
        self.server = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.texts_collection_name = f"file_{ts}_texts"
        self.images_collection_name = f"file_{ts}_images"
        self.tables_collection_name = f"file_{ts}_tables"
        self._connect_db()

        # Initialize embedding models
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
        """Connect to Qdrant client and initialize collections if needed"""
        self.client = QdrantClient(host=self.server, port=self.port)
        
        # Create collections for this knowledge base if they don't exist
        for collection_name in [self.texts_collection_name, self.images_collection_name, self.tables_collection_name]:
            try:
                self.client.get_collection(collection_name=collection_name)
                print(f"Collection {collection_name} already exists")
            except Exception as e:
                print(f"Creating collection {collection_name}")
                if collection_name == self.texts_collection_name:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config={
                            "embed": models.VectorParams(size=TEXT_EMB_DIM, distance=models.Distance.COSINE),
                            "cord": models.VectorParams(size=2, distance=models.Distance.EUCLID),
                        }
                    )
                elif collection_name == self.images_collection_name:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=IMG_EMB_DIM, distance=models.Distance.COSINE)
                    )
                elif collection_name == self.tables_collection_name:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=TABLE_EMB_DIM, distance=models.Distance.COSINE)
                    )
                else:
                    raise ValueError(f"Unknown collection name: {collection_name}")

    def _common_transform(self, data: dict) -> dict:
        """Transform common fields between different data types"""
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
        """Transform text data for Qdrant storage"""
        row = self._common_transform(data)
        txt = data.get("text", "")
        row.update({
            "text": txt,  # add flattened text
            "orig": data.get("orig"),
        })
        return row

    def image_transform(self, data: dict) -> dict:
        """Transform image data for Qdrant storage"""
        row = self._common_transform(data)
        image_info = data.get("image", {})
        uri = image_info.get("uri", "")
        encoded = uri.split(",", 1)[1] if "," in uri else uri
        img_bytes = base64.b64decode(encoded)
        with NamedTemporaryFile(suffix='.png') as tmp:
            tmp.write(img_bytes)
            tmp.flush()
            emb = list(self.image_model.embed([tmp.name]))[0]
        row.update({
            "image": encoded,
            "dpi": image_info.get("dpi"),
            "size": list(image_info.get("size", {}).values()),
            "type": image_info.get("mimetype"),
        })
        return row, emb

    def table_transform(self, chunk) -> dict:
        """Transform table data for Qdrant storage"""
        txt = chunk.text
        emb = list(self.table_model.embed([txt]))[0]
        return {"text": txt}, emb

    def save(self, file_name: str, data: dict, meta_data) -> dict:
        """Save data to Qdrant and return status information"""
        status = {
            "status": "success",
            "texts_collection_name": self.texts_collection_name,
            "images_collection_name": self.images_collection_name,
            "tables_collection_name": self.tables_collection_name,
        }
        logging.info(f"texts_collection_name: {self.texts_collection_name}")
        logging.info(f"images_collection_name: {self.images_collection_name}")
        logging.info(f"tables_collection_name: {self.tables_collection_name}")
        logging.info(f"file_name: {file_name}")
        # Process text data
        pure_texts = [t.get("text", "") for t in data.get("texts", [])]
        if pure_texts:
            embeds = list(self.text_model.embed(pure_texts))
            texts = [self.text_transform(t) for t in data.get("texts", [])]
            cords = [t.get("coord", []) for t in texts]

            # Insert into Qdrant
            points = []
            for i, text in enumerate(texts):
                points.append(models.PointStruct(
                    id=i,
                    vector={
                        "embed": embeds[i].tolist() if hasattr(embeds[i], 'tolist') else embeds[i],
                        # "cord": calculate_centroid(cords[i]) if len(cords[i])==4 else [0.0, 0.0]
                        "cord": one_y_point(cords[i]) if len(cords[i]) == 4 else [0.0, 0.0]
                    },
                    payload=text
                ))
            
            if points:
                self.client.upsert(
                    collection_name=self.texts_collection_name,
                    points=points
                )
        else:
            status["texts_collection_name"] = ""

        # Process image data
        pics = data.get("pictures", [])
        if pics:
            points = []
            for i, img in enumerate(pics):
                payload, vector = self.image_transform(img)
                points.append(models.PointStruct(
                    id=i,
                    vector=vector.tolist() if hasattr(vector, 'tolist') else vector,
                    payload=payload
                ))
            
            if points:
                self.client.upsert(
                    collection_name=self.images_collection_name,
                    points=points
                )
        else:
            status["images_collection_name"] = ""

        # Process table data
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
            
            points = []
            for i, chunk in enumerate(chunks):
                payload, vector = self.table_transform(chunk)
                points.append(models.PointStruct(
                    id=i,
                    vector=vector.tolist() if hasattr(vector, 'tolist') else vector,
                    payload=payload
                ))
            
            # Remove the temporary file
            os.remove(tmp.name)
            
            if points:
                self.client.upsert(
                    collection_name=self.tables_collection_name,
                    points=points
                )
        else:
            status["tables_collection_name"] = ""

        return status

    @staticmethod
    def list_all_collections(kb_name: str):
        """List all collections related to this knowledge base"""
        server = os.getenv("QDRANT_HOST", "qdrant")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=server, port=port)
        collections = client.get_collections().collections
        
        # Filter collections by kb_name
        kb_collections = []
        for collection in collections:
            if collection.name.startswith(f"file_") and collection.name.endswith(("_texts", "_images", "_tables")):
                kb_collections.append(collection.name)
        
        return kb_collections

    @staticmethod
    def list_all_collections_mongo(kb_name: str, kb_owner:str):
        """Get collection data from MongoDB for compatibility"""
        ms = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
        user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
        pwd = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")
        client = pymongo.MongoClient(ms, username=user, password=pwd)
        db = client["mortis"]
        coll = db.get_collection(kb_owner)
        return coll.find_one({"kb_name": kb_name}, {"_id": 0})


# Backward compatibility functions
def save_vec_store(kb_name: str, file_name: str, data: dict, meta_data) -> dict:
    """Save data to vector store using QdrantVecStore"""
    logging.info(f"Saving to vector store: {kb_name}, {file_name}")
    qdrantvec = QdrantVecStore(kb_name)
    return qdrantvec.save(file_name, data, meta_data)


def list_all_tables(kb_name: str):
    """List all tables (now collections) for compatibility"""
    return QdrantVecStore.list_all_collections(kb_name)


def list_all_tables_mongo(kb_name: str, kb_owner: str):
    """Get collection info from MongoDB for compatibility"""
    return QdrantVecStore.list_all_collections_mongo(kb_name, kb_owner)
