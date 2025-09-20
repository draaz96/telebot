import uvicorn
from fastapi import FastAPI
from routes.download import app as download_router
from bot import main as bot_main
import asyncio
import threading

app = FastAPI()
app.include_router(download_router)

def run_bot():
    asyncio.run(bot_main())

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Start FastAPI server
    start_server()