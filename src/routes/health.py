from fastapi import APIRouter, Response
import os

router = APIRouter()

@router.get("/health")
async def health_check(response: Response):
    # Check for either MONGODB_URI or MONGO_URL
    has_mongo = bool(os.getenv('MONGODB_URI') or os.getenv('MONGO_URL'))
    has_token = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
    
    status = {
        "status": "healthy" if (has_mongo and has_token) else "unhealthy",
        "checks": {
            "database": "connected" if has_mongo else "disconnected",
            "telegram_bot": "configured" if has_token else "not_configured"
        }
    }
    
    if not (has_mongo and has_token):
        response.status_code = 503
        missing = []
        if not has_mongo:
            missing.append("MONGODB_URI or MONGO_URL")
        if not has_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        status["message"] = f"Missing environment variables: {', '.join(missing)}"
    
    return status