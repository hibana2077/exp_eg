import os
import uvicorn
import redis
import pymongo
from fastapi import FastAPI, HTTPException
from datetime import datetime

# 常數設定，從環境變數中讀取設定
HOST = os.getenv("HOST", "127.0.0.1")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")

# Redis 資料庫設定，decode_responses=True 讓我們直接取得字串
user_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# MongoDB Database Setup
mongo_client = pymongo.MongoClient(MONGO_SERVER)

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

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)