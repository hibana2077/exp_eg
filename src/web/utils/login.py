import requests
import os

BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://localhost:8081")

def login(username: str, password: str):
    """
    登入函式，使用者名稱與密碼
    :param username: 使用者名稱
    :param password: 密碼
    :return: 登入結果
    """
    url = f"{BACKEND_SERVER}/login"
    data = {"username": username, "password": password}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200 and response.json().get("status") == "success":
        return True
    elif response.status_code == 400:
        error_message = response.json().get("message")
        return error_message
    else:
        return None