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
        if message.video:
            file = message.video
        elif message.document:
            file = message.document
        else:
            await message.reply_text("Please send a video file!")
            return

        # Download the file
        temp_path = Path('temp') / file.file_name
        file_obj = await context.bot.get_file(file.file_id)
        await file_obj.download_to_drive(temp_path)

        # Process file
        file_info = await file_handler.save_temp_file(str(temp_path), file.file_name)
        
        if not file_handler.is_valid_video(file_info['mime_type']):
            await message.reply_text("Invalid file type! Please send a video file (mp4, mkv, avi).")
            temp_path.unlink()
            return

        # Save to database
        file_id = await db.save_file(file_info)
        
        # Generate download link
        download_link = link_generator.generate_download_link(file_id, file.file_name)
        
        # Format response message
        response_text = (
            f"📁 File Name: {file.file_name}\n"
            f"💾 Size: {file_handler.format_size(file_info['size'])}\n"
            f"⌛ Link expires in: 2 hours\n\n"
            f"🔗 Download Link:\n{download_link}"
        )
        
        await message.reply_text(response_text)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        await message.reply_text("Sorry, there was an error processing your file. Please try again.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add video/document handler
    application.add_handler(MessageHandler(
        (filters.VIDEO | filters.Document.VIDEO | filters.Document.MimeType("video/mp4") |
         filters.Document.MimeType("video/x-matroska") | filters.Document.MimeType("video/x-msvideo")),
        handle_video
    ))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()