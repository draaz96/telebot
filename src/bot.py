import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from utils.database import Database
from utils.file_handler import FileHandler
from utils.link_generator import LinkGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
db = Database()
file_handler = FileHandler()
link_generator = LinkGenerator()

# Initialize bot with token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Welcome! Forward me any video file (mp4, mkv, avi) and I will generate a download link for you.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
Here's how to use me:
1. Forward any video file to me
2. I will process it and generate a download link
3. The link will be valid for 2 hours
4. Supported formats: mp4, mkv, avi, and other video formats
    """
    await update.message.reply_text(help_text)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video files and generate download links."""
    try:
        # Get the file
        message = update.message
        logger.info(f"Received message: {message.message_id}")
        
        if message.video:
            file = message.video
            logger.info("Received video file")
        elif message.document:
            file = message.document
            logger.info("Received document file")
        else:
            logger.warning("No video or document in message")
            await message.reply_text("Please send a video file!")
            return

        logger.info(f"Processing file: {file.file_name}")

        # Create temp directory if it doesn't exist
        temp_dir = Path('temp')
        temp_dir.mkdir(exist_ok=True)
        
        # Download the file
        temp_path = temp_dir / file.file_name
        logger.info(f"Downloading to: {temp_path}")
        file_obj = await context.bot.get_file(file.file_id)
        await file_obj.download_to_drive(temp_path)
        logger.info("File downloaded successfully")

        # Process file
        file_info = await file_handler.save_temp_file(str(temp_path), file.file_name)
        logger.info(f"File info: {file_info}")
        
        if not file_handler.is_valid_video(file_info['mime_type']):
            logger.warning(f"Invalid mime type: {file_info['mime_type']}")
            await message.reply_text("Invalid file type! Please send a video file (mp4, mkv, avi).")
            temp_path.unlink()
            return

        # Ensure database connection
        await db.connect()
        if not db.client:
            logger.error("Database connection failed")
            await message.reply_text("Sorry, database connection failed. Please try again later.")
            return

        # Save to database
        file_id = await db.save_file(file_info)
        logger.info(f"Saved to database with ID: {file_id}")
        
        # Generate download link
        download_link = link_generator.generate_download_link(file_id, file.file_name)
        logger.info(f"Generated download link: {download_link}")
        
        # Format response message
        response_text = (
            f"📁 File Name: {file.file_name}\n"
            f"💾 Size: {file_handler.format_size(file_info['size'])}\n"
            f"⌛ Link expires in: 2 hours\n\n"
            f"🔗 Download Link:\n{download_link}"
        )
        
        await message.reply_text(response_text)
        logger.info("Response sent to user")
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        await message.reply_text("Sorry, there was an error processing your file. Please try again.")

async def main(application: Application):
    """Initialize the bot with handlers."""
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add video/document handler
    application.add_handler(MessageHandler(
        (filters.VIDEO |
         filters.Document.VIDEO |
         filters.Document.MimeType("video/mp4") |
         filters.Document.MimeType("video/x-matroska") |
         filters.Document.MimeType("video/x-msvideo") |
         filters.Document.VIDEO |
         filters.Document.FileExtension("mkv") |
         filters.Document.FileExtension("mp4") |
         filters.Document.FileExtension("avi")),
        handle_video
    ))

    # Start polling in background
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    main()