import infinity
import datetime
import pymongo
import os
import base64

# fastembed is a library powered by Qdrant
from fastembed import TextEmbedding
from fastembed import ImageEmbedding

from cfg.emb_settings import EMB_MODEL,IMG_EMB_MODEL
from cfg.table_format import TEXT_FORMAT, IMAGE_FORMAT

def text_transform(data:dict)->dict:
    embedding_model = TextEmbedding(model_name=EMB_MODEL)
    embeddings_list = list(embedding_model.embed(data['text']))
    return {
         "self_ref": data["self_ref"],
         "parent": data["parent"]["$ref"],
         "content_layer": data["content_layer"],
         "label": data["label"],
         "page": data["prov"][0]["page_no"],
         "coord": list(data["prov"][0]["bbox"].values())[:4],
         "coord_origin": data["prov"][0]["bbox"]["coord_origin"],
         "orig": data["orig"],
         "text": data["text"],
         "embedding":embeddings_list[0]
    }

def image_transform(data:dict)->dict:
    encoded = data["image"]["uri"].split(",")[1]
    image_data = base64.b64decode(encoded)
    with open("temp.png", "wb") as f:f.write(image_data)
    img_embedding_model = ImageEmbedding(model_name=IMG_EMB_MODEL)
    embeddings_list = list(img_embedding_model.embed(["temp.png"]))
    os.remove("temp.png")
    return {
        "self_ref": data["self_ref"],
        "parent": data["parent"]["$ref"],
        "content_layer": data["content_layer"],
        "label": data["label"],
        "page": data["prov"][0]["page_no"],
        "coord": list(data["prov"][0]["bbox"].values())[:4],
        "coord_origin": data["prov"][0]["bbox"]["coord_origin"],
        "image": encoded,
        "dpi": data["dpi"],
        "size": list(data["image"]["size"].values()),
        "type": data["type"],
        "embedding":embeddings_list[0]
    }

def save_vec_store(kb_name:str, file_name:str, data:dict):
    status = {
        "status": "success",
        "texts_table_name": "file_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_texts",
        "images_table_name": "file_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_images"
    }

    # Connect to InfinityDB
    SERVER_IP_ADDRESS = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT = os.getenv("INFINITY_PORT", "23817")
    infinity_obj = infinity.connect(infinity.NetworkAddress(SERVER_IP_ADDRESS, INFINITY_PORT))
    
    # select db
    try:
        # Create a database if it doesn't exist
        # Check if the database already exists
        res = infinity_obj.list_databases()
        if kb_name.lower() not in res.db_names:
            # Create the database
            db_object = infinity_obj.create_database(kb_name.lower())
        else:
            # Connect to the existing database
            db_object = infinity_obj.get_database(kb_name.lower())
    except Exception as e:
        status["status"] = str(e) + " at " + str(e.__traceback__.tb_lineno)
        return status

    # Create a table for texts
    text_table_name = status["texts_table_name"]
    texts_table = db_object.create_table(text_table_name, TEXT_FORMAT)
    for i in range(len(data['texts'])):texts_table.insert([text_transform(data['texts'][i])])

    # Create a table for pictures if needed
    image_table_name = status["images_table_name"]
    if data['pictures']:
        images_table = db_object.create_table(image_table_name, IMAGE_FORMAT)
        for i in range(len(data['pictures'])):images_table.insert([image_transform(data['pictures'][i])])
    else:
        status["images_table_name"] = ""

    # Close the connection
    infinity_obj.disconnect()
    return status

def list_all_tables(kb_name:str):
    # Connect to InfinityDB
    SERVER_IP_ADDRESS = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT = os.getenv("INFINITY_PORT", "23817")
    infinity_obj = infinity.connect(infinity.NetworkAddress(SERVER_IP_ADDRESS, INFINITY_PORT))
    
    # Create a database if it doesn't exist
    db_object = infinity_obj.get_database(kb_name.lower())
    
    # List all tables in the database
    tables = db_object.list_tables()
    
    # Close the connection
    infinity_obj.disconnect()
    
    return tables

def list_all_tables_mongo(kb_name:str):

    MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
    MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")

    # Connect to MongoDB
    mongo_client = pymongo.MongoClient(
        MONGO_SERVER,
        username=MONGO_INITDB_ROOT_USERNAME,
        password=MONGO_INITDB_ROOT_PASSWORD
    )
    mongo_db = mongo_client["mortis"]
    mongo_collection = mongo_db["index_info"]
    
    # Find the knowledge base by name
    kb_info = mongo_collection.find_one({"kb_name": kb_name}, {"_id": 0})

    return kb_info