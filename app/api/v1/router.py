from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(chat_router)
