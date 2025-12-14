import json
from typing import Any

import httpx


class MCPContextService:
    """Lightweight HTTP client for interacting with the MCP server."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    async def initialize_session(self, session_id: str, user_profile: dict[str, Any]) -> None:
        payload = {"session_id": session_id, "user_profile": user_profile}
        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=10.0) as client:
            await client.post("/sessions/init", content=json.dumps(payload))

    async def get_session_context(self, session_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=10.0) as client:
            response = await client.get(f"/sessions/{session_id}/context")
            response.raise_for_status()
            return response.json()

    async def push_turn(self, session_id: str, turn: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=10.0) as client:
            response = await client.post(f"/sessions/{session_id}/turns", content=json.dumps(turn))
            response.raise_for_status()
            return response.json()
