TEXT_FORMAT = {
    "self_ref": {"type": "varchar"},             # 儲存 texts 自身的參考 ID，如 "#/texts/30"
    "parent": {"type": "varchar"},               # 儲存父節點參考（例如 "#/body"）
    # "children": {"type": "array,varchar"},       # 儲存子節點的陣列（此例中為空陣列）
    "content_layer": {"type": "varchar"},        # 儲存內容層級，如 "body"
    "label": {"type": "varchar"},                # 儲存標籤名稱，如 "text"
    "page": {"type": "int16"},                    # 儲存頁面編號
    "coord": {"type": "vector,4,float"},            # 儲存座標
    "coord_origin": {"type": "varchar"},          # 儲存座標來源
    "orig": {"type": "varchar"},                 # 原始文字內容
    "text": {"type": "varchar"},                  # 解析後或顯示用的文字內容
    "embedding": {"type": "vector,1024,float"}, # 儲存嵌入向量
}

IMAGE_FORMAT = {
    "self_ref": {"type": "varchar"},             # 儲存 images 自身的參考 ID，如 "#/images/2"
    "parent": {"type": "varchar"},               # 儲存父節點參考（例如 "#/body"）
    "content_layer": {"type": "varchar"},        # 儲存內容層級，如 "body"
    "label": {"type": "varchar"},                # 儲存標籤名稱，如 "picture"
    "page": {"type": "int16"},                    # 儲存頁面編號
    "coord": {"type": "vector,4,float"},            # 儲存座標
    "coord_origin": {"type": "varchar"},          # 儲存座標來源
    "image": {"type": "varchar"}, # 儲存圖片的 base64 編碼
    "dpi": {"type": "int16"}, # 儲存圖片的 DPI
    "size": {"type": "vector,2,float"}, # 儲存圖片的大小
    "type": {"type": "varchar"}, # 儲存圖片的類型，如 "image/png"
    "embedding": {"type": "vector,512,float"}, # 儲存嵌入向量
}