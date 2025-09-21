import os
import uvicorn
from fastapi import FastAPI
from routes.download import router as download_router
from routes.health import router as health_router
from telegram.ext import Application
from bot import main as bot_main
import asyncio
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

# Global variable for the bot application
bot_app = None

@app.on_event("startup")
async def startup_event():
    """Start the bot when the FastAPI server starts"""
    global bot_app
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return

        # Initialize bot
        bot_app = Application.builder().token(token).build()
        
        # Set up handlers (from bot.main)
        await bot_main(bot_app)
        
        # Start the bot
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.update_bot_data({})  # Initialize bot data
        
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the bot when the FastAPI server stops"""
    global bot_app
    if bot_app:
        try:
            await bot_app.stop()
            await bot_app.shutdown()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")

def start_server():
    """Start the FastAPI server"""
    try:
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