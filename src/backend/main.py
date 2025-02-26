import uvicorn
import os
import redis
from datetime import datetime
from dataclasses import dataclass
from blacksheep import Application, FromJSON, FromQuery, get, post

# Const
HOST = os.getenv("HOST", "127.0.0.1")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

# REDIS db setup
user_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# dataclass
@dataclass
class User:
    username: str
    password: str

app = Application()

@get("/")
async def home():
    return f"Hello, World! {datetime.utcnow().isoformat()}"

@post("/register")
async def register(user: User = FromJSON()):
    if user_db.exists(user.username):
        return {"status": "error", "message": "User already exists"}
    user_db.set(user.username, user.password)
    return {"status": "success", "message": "User registered successfully"}

@post("/login")
async def login(user: User = FromJSON()):
    if not user_db.exists(user.username):
        return {"status": "error", "message": "User does not exist"}
    if user_db.get(user.username).decode() != user.password:
        return {"status": "error", "message": "Invalid password"}
    return {"status": "success", "message": "Login successful"}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)