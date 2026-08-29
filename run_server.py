import asyncio
import uvicorn
from app.main import app

if __name__ == "__main__":
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

