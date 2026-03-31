from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.config import Settings

router = APIRouter()
_settings = Settings()


@router.get("/api/config")
async def get_config():
    return JSONResponse({"stadia_api_key": _settings.STADIA_API_KEY})
