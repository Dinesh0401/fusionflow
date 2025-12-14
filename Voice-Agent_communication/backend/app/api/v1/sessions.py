from uuid import uuid4

from fastapi import APIRouter, Depends

from ...core.config import get_settings
from ...schemas.session import SessionCreateRequest, SessionCreateResponse, SessionStateResponse
from ...services.mcp_context import MCPContextService

router = APIRouter()


def get_context_service(settings=Depends(get_settings)) -> MCPContextService:
    return MCPContextService(base_url=settings.mcp_server_url, api_key=settings.mcp_api_key)


@router.post("", response_model=SessionCreateResponse)
async def create_session(payload: SessionCreateRequest, context_service: MCPContextService = Depends(get_context_service)) -> SessionCreateResponse:
    session_id = str(uuid4())
    await context_service.initialize_session(session_id=session_id, user_profile=payload.user_profile.dict())
    return SessionCreateResponse(session_id=session_id, mode=payload.mode)


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str, context_service: MCPContextService = Depends(get_context_service)) -> SessionStateResponse:
    context_snapshot = await context_service.get_session_context(session_id=session_id)
    return SessionStateResponse(session_id=session_id, context=context_snapshot)
