from uuid import UUID

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    items: list
    total: int


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    raw_key: str | None = None
