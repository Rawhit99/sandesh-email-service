from fastapi import APIRouter
from middleware.rate_limit import limiter

router = APIRouter()


@router.get("/health")
@limiter.exempt
async def health_check():
    return {
        "status": "healthy",
        "message": "Email Notification System API is running",
    }
