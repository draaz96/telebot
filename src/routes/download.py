from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from utils.database import Database
from utils.link_generator import LinkGenerator
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()
db = Database()
link_generator = LinkGenerator()

@router.get("/download/{token}")
async def download_file(token: str):
    try:
        # Ensure database is connected
        await db.connect()
        if not db.client:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )

        # Verify and decrypt token
        file_data = link_generator.verify_link(token)
        
        # Get file info from database
        file_info = await db.get_file(file_data['file_id'])
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
            
        file_path = Path(file_info['path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        # Update download count
        try:
            await db.update_download_count(file_data['file_id'])
        except Exception as e:
            logger.warning(f"Failed to update download count: {str(e)}")
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=file_info['original_name'],
            media_type=file_info['mime_type']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing download: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")