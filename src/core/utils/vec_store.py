import os
import datetime
import base64
import io
import pprint
from tempfile import NamedTemporaryFile
import infinity  # type: ignore
import pymongo
from transformers import AutoTokenizer
from docling.chunking import HybridChunker  # type: ignore
from fastembed import TextEmbedding, ImageEmbedding  # type: ignore
from cfg.emb_settings import EMB_MODEL, IMG_EMB_MODEL, TABLE_EMB_MODEL, TABLE_CHUNK_MAX_TOKENS
from cfg.table_format import TEXT_FORMAT, IMAGE_FORMAT, TABLE_FORMAT
from .parse import table_convert, merge_adjacent_tables


class VecStore:
    def __init__(self, kb_name: str):
        self.kb_name = kb_name.lower()
        self.server = os.getenv("INFINITY_HOST", "localhost")
        self.port = os.getenv("INFINITY_PORT", "23817")
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
        self.infinity_obj = infinity.connect(infinity.NetworkAddress(self.server, self.port))
        dbs = self.infinity_obj.list_databases().db_names
        if self.kb_name not in dbs:
            self.db = self.infinity_obj.create_database(self.kb_name)
        else:
            self.db = self.infinity_obj.get_database(self.kb_name)

    def _disconnect(self):
        self.infinity_obj.disconnect()

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
            emb = list(self.image_model.embed([tmp.name]))[0]
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
        return {"text": txt, "embedding": list(self.table_model.embed([txt]))[0]}

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
        texts = [self.text_transform(t) for t in data.get("texts", [])]
        for i, text in enumerate(texts):
            text['embedding'] = embeds[i]
        tbl_txt = self.db.create_table(self.texts_table_name, TEXT_FORMAT)
        if texts:
            tbl_txt.insert(texts)
        # Images
        pics = [self.image_transform(i) for i in data.get("pictures", [])]
        if pics:
            tbl_img = self.db.create_table(self.images_table_name, IMAGE_FORMAT)
            tbl_img.insert(pics)
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
                tbl_tab = self.db.create_table(self.tables_table_name, TABLE_FORMAT)
                tbl_tab.insert(tables)
        else:
            status["tables_table_name"] = ""
        self._disconnect()
        return status

    @staticmethod
    def list_all_tables(kb_name: str):
        server = os.getenv("INFINITY_HOST", "localhost")
        port = os.getenv("INFINITY_PORT", "23817")
        inf = infinity.connect(infinity.NetworkAddress(server, port))
        db = inf.get_database(kb_name.lower())
        tables = db.list_tables()
        inf.disconnect()
        return tables

    @staticmethod
    def list_all_tables_mongo(kb_name: str):
        ms = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
        user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
        pwd = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")
        client = pymongo.MongoClient(ms, username=user, password=pwd)
        db = client["mortis"]
        coll = db.get_collection("index_info")
        return coll.find_one({"kb_name": kb_name}, {"_id": 0})

# Backward compatibility functions

def save_vec_store(kb_name: str, file_name: str, data: dict, meta_data) -> dict:
    return VecStore(kb_name).save(file_name, data, meta_data)


def list_all_tables(kb_name: str):
    return VecStore.list_all_tables(kb_name)


def list_all_tables_mongo(kb_name: str):
    return VecStore.list_all_tables_mongo(kb_name)