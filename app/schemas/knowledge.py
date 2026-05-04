from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class KnowledgeTextIngestRequest(BaseModel):
    title: str
    text: str


class KnowledgeUrlIngestRequest(BaseModel):
    title: str
    url: HttpUrl


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    title: str
    source_type: str
    status: str
    chunk_count: int
    created_at: datetime
