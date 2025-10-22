# services/backend/app/api/__init__.py
from fastapi import APIRouter
from .mood import router as mood_router
from .users import router as users_router
from .chat import router as chat_router

api_router = APIRouter()
api_router.include_router(mood_router)
api_router.include_router(users_router)
api_router.include_router(chat_router)
