import infinity
import os

from cfg.table_format import TEXT_FORMAT

def text_transform(data:dict)->dict:
    return {
         "self_ref": data["self_ref"],
         "parent": data["parent"]["$ref"],
        #  "children": data["children"],
         "content_layer": data["content_layer"],
         "label": data["label"],
         "page": data["prov"][0]["page_no"],
         "coord": list(data["prov"][0]["bbox"].values())[:4],
         "coord_origin": data["prov"][0]["bbox"]["coord_origin"],
         "orig": data["orig"],
         "text": data["text"]
    }

def save_vec_store(kb_name:str, file_name:str, data:dict):
    status = {
        "status": "success",
        "texts_table_name": file_name.split(".")[0],
        # "pictures_table_name": file_name.split(".")[0] + "_pictures"
    }

    # Connect to InfinityDB
    SERVER_IP_ADDRESS = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT = os.getenv("INFINITY_PORT", "23817")
    infinity_obj = infinity.connect(infinity.NetworkAddress(SERVER_IP_ADDRESS, INFINITY_PORT))
    
    # Create a database if it doesn't exist
    db_object = infinity_obj.create_database(kb_name.lower())
    table_name = file_name.split(".")[0]
    texts_table = db_object.create_table(table_name, TEXT_FORMAT)
    for i in range(len(data['texts'])):texts_table.insert([text_transform(data['texts'][i])])

    # Create a table for pictures if needed
    # ...

    # Close the connection
    infinity_obj.close()
    return status