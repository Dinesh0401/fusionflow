from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionMode(str, Enum):
    mock_interview = "mock_interview"
    conversation = "conversation"
    group_discussion = "group_discussion"


class UserProfile(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    language_level: str = Field(..., description="CEFR-like label for proficiency")
    target_role: str | None = Field(None, description="Role or goal for personalization")


class SessionCreateRequest(BaseModel):
    mode: SessionMode
    user_profile: UserProfile


class SessionCreateResponse(BaseModel):
    session_id: str
    mode: SessionMode


class SessionStateResponse(BaseModel):
    session_id: str
    context: dict[str, Any]
