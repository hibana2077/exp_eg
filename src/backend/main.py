import os
import uvicorn
import redis
import pymongo
from minio import Minio
from fastapi import FastAPI, HTTPException
from datetime import datetime

# 常數設定，從環境變數中讀取設定
HOST = os.getenv("HOST", "127.0.0.1")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")

# Redis 資料庫設定，decode_responses=True 讓我們直接取得字串
user_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# MongoDB Database Setup
mongo_client = pymongo.MongoClient(
    MONGO_SERVER,
    username=MONGO_INITDB_ROOT_USERNAME,
    password=MONGO_INITDB_ROOT_PASSWORD
)

# MinIO 客戶端設定
minio_client = Minio(
    "minio:9000",
    access_key=MINIO_USER,
    secret_key=MINIO_PASSWORD,
    secure=False,
)

app = FastAPI()

# 首頁路由
@app.get("/")
async def home():
    return {"message": f"Hello, World! {datetime.utcnow().isoformat()}"}

# 註冊路由
@app.post("/register")
async def register(user: dict):
    if user_db.exists(user.get("username")):
        raise HTTPException(status_code=400, detail="User already exists")
    user_db.set(user.get("username"), user.get("password"))
    return {"status": "success", "message": "User registered successfully"}

# 登入路由
@app.post("/login")
async def login(user: dict):
    if not user_db.exists(user["username"]):
        raise HTTPException(status_code=400, detail="User does not exist")
    if user_db.get(user["username"]) != user["password"]:
        raise HTTPException(status_code=400, detail="Invalid password")
    return {"status": "success", "message": "Login successful"}

@app.post("/new_kb")
async def new_kb(kb: dict):
    """
    {
        "name": "Knowledge Base Name",
        "desc": "Knowledge Base Description",
        "icon": "Knowledge Base Icon",
        "owner": "Owner Username"
    }
    """
    # check if the knowledge base already exists
    if mongo_client["knowledge_base"].kb.find_one({"name": kb["name"], "owner": kb["owner"]}):
        raise HTTPException(status_code=400, detail="Knowledge base already exists")
    # insert the new knowledge base into MongoDB
    mongo_client["knowledge_base"].kb.insert_one({
        "name": kb["name"],
        "desc": kb["desc"],
        "icon": kb["icon"],
        "owner": kb["owner"],
        "created_at": datetime.utcnow()
    })
    return {"status": "success", "message": "Knowledge base entry created"}

@app.get("/list_all_kb/{owner_username}")
async def list_all_kb(owner_username: str):
    """
    List all knowledge bases for a specific owner.
    
    Parameters:
    - owner_username: Username of the owner whose knowledge bases to list
    
    Returns:
    - List of knowledge bases owned by the specified user
    """
    # Find all knowledge bases belonging to the specified owner
    kb_list = list(mongo_client["knowledge_base"].kb.find(
        {"owner": owner_username},
        {"_id": 0}  # Exclude the MongoDB _id field from the results
    ))
    
    return {
        "status": "success",
        "count": len(kb_list),
        "data": kb_list
    }


@app.get("/get_kb/{owner_username}/{kb_name}")
async def get_kb(owner_username: str, kb_name: str):
    """
    Get a specific knowledge base by owner and name.
    
    Parameters:
    - owner_username: Username of the owner
    - kb_name: Name of the knowledge base to retrieve
    
    Returns:
    - Knowledge base details if found
    """
    # Find the specific knowledge base
    kb = mongo_client["knowledge_base"].kb.find_one(
        {"owner": owner_username, "name": kb_name},
        {"_id": 0}  # Exclude the MongoDB _id field from the results
    )
    
    # If knowledge base doesn't exist, return 404 error
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {
        "status": "success",
        "data": kb
    }

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)