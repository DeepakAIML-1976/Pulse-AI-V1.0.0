from fastapi import APIRouter
from .mood import router as mood_router

api_router = APIRouter()
api_router.include_router(mood_router)
