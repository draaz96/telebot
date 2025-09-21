import os
import magic
from datetime import datetime
from pathlib import Path

ALLOWED_MIME_TYPES = [
    'video/mp4',
    'video/x-matroska',  # mkv
    'video/x-msvideo',   # avi
    'video/quicktime',   # mov
    'video/x-ms-wmv'     # wmv
]

class FileHandler:
    def __init__(self):
        self.temp_dir = Path('temp')
        self.temp_dir.mkdir(exist_ok=True)

    async def save_temp_file(self, file_path: str, file_name: str) -> dict:
        """
        Save file information and return metadata
        """
        file_mime = magic.from_file(file_path, mime=True)
        file_size = os.path.getsize(file_path)
        
        return {
            'original_name': file_name,
            'mime_type': file_mime,
            'size': file_size,
            'path': str(file_path),
            'created_at': datetime.utcnow()
        }

    def is_valid_video(self, mime_type: str) -> bool:
        """
        Check if the file is a valid video format
        """
        logger.info(f"Checking mime type: {mime_type}")
        is_valid = mime_type in ALLOWED_MIME_TYPES
        if not is_valid:
            logger.warning(f"Invalid mime type: {mime_type}. Allowed types: {ALLOWED_MIME_TYPES}")
        return is_valid

    def format_size(self, size_in_bytes: int) -> str:
        """
        Convert size in bytes to human readable format
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} TB"