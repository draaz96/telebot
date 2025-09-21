import os
import uvicorn
from fastapi import FastAPI
from routes.download import router as download_router
from routes.health import router as health_router
from telegram.ext import Application
from bot import main as bot_main
import asyncio
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for the bot application
bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events for setup/cleanup."""
    try:
        # Initialize MongoDB connection
        await init_mongodb()
        logger.info("MongoDB connection initialized")
        
        # Initialize bot 
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        
        application = Application.builder().token(token).build()
        logger.info("Bot application built successfully")
        
        # Start bot in background task
        task = asyncio.create_task(main(application))
        app.state.bot_task = task
        app.state.application = application
        
        logger.info("Bot initialization completed")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
        
    finally:
        # Cleanup
        try:
            logger.info("Starting cleanup...")
            if hasattr(app.state, 'application'):
                await app.state.application.updater.stop()
                await app.state.application.shutdown()
                logger.info("Bot shutdown complete")
            
            await cleanup_mongodb()
            logger.info("MongoDB connection closed")
            
            if hasattr(app.state, 'bot_task'):
                app.state.bot_task.cancel()
                try:
                    await app.state.bot_task
                except asyncio.CancelledError:
                    pass
                logger.info("Bot task cancelled")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

# Create FastAPI app with lifespan
app = FastAPI(title="Telegram File Bot", lifespan=lifespan)

# Add routes
app.include_router(download_router, prefix="/api")
app.include_router(health_router)

def start_server():
    """Start the FastAPI server"""
    try:
        port = int(os.getenv('PORT', '8080'))
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            loop="asyncio"
        )
    except Exception as e:
        logger.error(f"Server crashed: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("Starting FastAPI server")
        start_server()
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")