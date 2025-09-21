import os
import uvicorn
from fastapi import FastAPI
from routes.download import router as download_router
from routes.health import router as health_router
from bot import main as bot_main
import asyncio
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Telegram File Bot")

# Add routes
app.include_router(download_router, prefix="/api")
app.include_router(health_router)

def run_bot():
    try:
        asyncio.run(bot_main())
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

def start_server():
    try:
        port = int(os.getenv('PORT', '8000'))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Server crashed: {str(e)}")

if __name__ == "__main__":
    try:
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started")
        
        # Start FastAPI server
        logger.info("Starting FastAPI server")
        start_server()
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")