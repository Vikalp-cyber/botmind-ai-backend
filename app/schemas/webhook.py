from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class WebhookEndpointCreate(BaseModel):
    provider: str
    url: HttpUrl
    secret: str | None = None


class WebhookEndpointResponse(BaseModel):
    id: UUID
    provider: str
    url: str
    is_active: bool
    created_at: datetime
