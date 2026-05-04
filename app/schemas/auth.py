from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=255)
    tenant_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    tenant_slug: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: UUID
    role: str


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    role: str
    type: str


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    @classmethod
    def from_model(cls, user):
        return cls(
            id=user.id,
            tenant_id=user.tenant_id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )
