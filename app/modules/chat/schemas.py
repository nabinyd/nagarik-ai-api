from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    session_id: int | None = Field(default=None, gt=0)


class CreateChatSessionRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip() if value is not None else None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value


class RenameChatSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Literal["user", "assistant"]
    content: str
    sources: list[dict[str, Any]] | None = None
    created_at: datetime


class ChatSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class ChatSessionResponse(ChatSessionSummary):
    messages: list[ChatMessageResponse]


class ChatAnswerResponse(BaseModel):
    session_id: int
    answer: str
    sources: list[dict[str, Any]]
    metadata: dict[str, Any]