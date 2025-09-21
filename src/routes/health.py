from fastapi import APIRouter, Response
import os

router = APIRouter()

@router.get("/health")
async def health_check(response: Response):
    # Check if required environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'MONGODB_URI']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        response.status_code = 503
        return {
            "status": "unhealthy",
            "message": f"Missing environment variables: {', '.join(missing_vars)}"
        }
    
    return {"status": "healthy"}