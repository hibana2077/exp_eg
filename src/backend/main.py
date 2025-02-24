import uvicorn
import os
import redis
from datetime import datetime
from blacksheep import Application, get

HOST = os.getenv("HOST", "127.0.0.1")

app = Application()

@get("/")
async def home():
    return f"Hello, World! {datetime.utcnow().isoformat()}"

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)