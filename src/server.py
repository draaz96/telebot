import os
import uvicorn
from fastapi import FastAPI
from routes.download import router as download_router
from routes.health import router as health_router
from bot import main as bot_main
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

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

# Create a new event loop for the bot
bot_loop = asyncio.new_event_loop()

def run_bot_forever():
    """Run the bot in its own event loop"""
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_until_complete(bot_main())

@app.on_event("startup")
async def startup_event():
    """Start the bot when the FastAPI server starts"""
    try:
        # Start the bot in a thread pool
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(run_bot_forever)
        logger.info("Bot thread started")
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

def start_server():
    """Start the FastAPI server"""
    try:
        # Use PORT environment variable with fallback to 8080 for Railway
        port = int(os.getenv('PORT', '8080'))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Server crashed: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("Starting FastAPI server")
        start_server()
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
    finally:
        # Cleanup
        if bot_loop.is_running():
            bot_loop.stop()
        bot_loop.close()