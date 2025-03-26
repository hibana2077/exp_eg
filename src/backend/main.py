import os
import uvicorn
import redis
import pymongo
from minio import Minio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# 常數設定，從環境變數中讀取設定
HOST = os.getenv("HOST", "127.0.0.1")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")

# 設定SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

# ---

app = FastAPI()

# ---

# 使用者模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# 創建資料庫表格
Base.metadata.create_all(bind=engine)

# 依賴注入：資料庫會話
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 首頁路由
@app.get("/")
async def home():
    return {"message": f"Hello, World! {datetime.utcnow().isoformat()}"}

# 註冊路由
@app.post("/register")
async def register(user: dict, db: Session = Depends(get_db)):
    # 檢查使用者是否已存在
    existing_user = db.query(User).filter(User.username == user.get("username")).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # 創建新使用者
    new_user = User(username=user.get("username"), password=user.get("password"))
    db.add(new_user)
    
    try:
        db.commit()
        return {"status": "success", "message": "User registered successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")

# 登入路由
@app.post("/login")
async def login(user: dict, db: Session = Depends(get_db)):
    # 查找使用者
    existing_user = db.query(User).filter(User.username == user.get("username")).first()
    
    # 驗證使用者
    if not existing_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    if existing_user.password != user.get("password"):
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
    
    # create a bucket in MinIO using the knowledge base name
    bucket_name = kb["name"].lower().replace(" ", "_")  # 將空格替換為下劃線並轉為小寫，確保符合 bucket 命名規則
    try:
        # 檢查 bucket 是否已存在
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except Exception as e:
        # 如果創建 bucket 失敗，拋出異常
        raise HTTPException(status_code=500, detail=f"Failed to create MinIO bucket: {str(e)}")
    
    # insert the new knowledge base into MongoDB
    mongo_client["knowledge_base"].kb.insert_one({
        "name": kb["name"],
        "desc": kb["desc"],
        "icon": kb["icon"],
        "owner": kb["owner"],
        "bucket_name": bucket_name,  # 儲存 bucket 名稱
        "created_at": datetime.utcnow()
    })
    
    return {"status": "success", "message": "Knowledge base entry and MinIO bucket created"}

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