from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LeadResponse(BaseModel):
    id: UUID
    session_id: UUID | None
    name: str | None
    email: EmailStr | None
    phone: str | None
    tag: str
    created_at: datetime
