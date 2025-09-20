from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from utils.database import Database
from utils.link_generator import LinkGenerator
import os
from pathlib import Path

app = FastAPI()
db = Database()
link_generator = LinkGenerator()

@app.get("/download/{token}")
async def download_file(token: str):
    try:
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
        await db.update_download_count(file_data['file_id'])
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=file_info['original_name'],
            media_type=file_info['mime_type']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")