from fastapi import APIRouter

from . import sessions, speech

api_router = APIRouter()
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
