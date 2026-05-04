from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Citation(BaseModel):
    knowledge_base_id: UUID
    title: str
    chunk_index: int
    score: float
    excerpt: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    session_id: str = Field(min_length=1, max_length=255)
    tenant_id: UUID


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tenant_id: UUID
    cached: bool = False
    citations: list[Citation] = Field(default_factory=list)
    lead_captured: bool = False


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime


class SessionResponse(BaseModel):
    id: UUID
    external_id: str
    channel: str
    created_at: datetime
    last_activity_at: datetime | None
