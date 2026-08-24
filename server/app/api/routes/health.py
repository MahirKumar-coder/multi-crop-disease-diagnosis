from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()

@router.get("", tags=["System"])
@router.get("/", tags=["System"])
async def health_check():
    return {"status": "online", "version": settings.VERSION}
