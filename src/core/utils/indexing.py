import infinity
import datetime
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

def indexing(db_name:str,table_name:str):
    INFINITY_HOST = os.getenv("INFINITY_HOST", "localhost")
    INFINITY_PORT = os.getenv("INFINITY_PORT", 8080)
    # Initialize connection
    infinity_obj = infinity.connect(infinity.NetworkAddress(INFINITY_HOST, INFINITY_PORT))
    db_obj = infinity_obj.get_database(db_name)
    table_obj = db_obj.get_table(table_name)

    index_name = 'text_index_in_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    res_index = table_obj.create_index(
        index_name,
        infinity_obj.index.IndexInfo("text", infinity_obj.index.IndexType.FullText,{"analyzer": "rag"}),
        infinity_obj.common.ConflictType.Error,
    )
    # Close the connection
    infinity_obj.disconnect()
    return index_name

def add_index_into_condiction(condiction, index_name:str):
    