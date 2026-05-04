import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_api_key, hash_password, verify_password
from app.db.models import APIKey, Tenant, User, UserRole
from app.schemas.common import APIKeyResponse
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def signup(self, payload: SignupRequest) -> TokenResponse:
        existing_tenant = await self.session.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
        if existing_tenant:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")

        tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug)
        user = User(
            tenant=tenant,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.ADMIN,
        )
        self.session.add_all([tenant, user])
        await self.session.commit()
        await self.session.refresh(user)
        return TokenResponse(
            access_token=create_access_token(str(user.id), str(user.tenant_id), user.role),
            tenant_id=user.tenant_id,
            role=user.role,
        )

    async def login(self, payload: LoginRequest) -> TokenResponse:
        statement = (
            select(User, Tenant)
            .join(Tenant, Tenant.id == User.tenant_id)
            .where(Tenant.slug == payload.tenant_slug, User.email == payload.email)
        )
        result = await self.session.execute(statement)
        row = result.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        user, tenant = row
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenResponse(
            access_token=create_access_token(str(user.id), str(tenant.id), user.role),
            tenant_id=tenant.id,
            role=user.role,
        )

    async def get_active_user(self, user_id: UUID, tenant_id: str):
        statement = select(User).where(
            User.id == user_id,
            User.tenant_id == UUID(tenant_id),
            User.is_active.is_(True),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_api_key(self, *, tenant_id: UUID, name: str) -> APIKeyResponse:
        raw_key = f"bm_{secrets.token_urlsafe(32)}"
        api_key = APIKey(
            tenant_id=tenant_id,
            name=name,
            hashed_key=hash_api_key(raw_key),
        )
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return APIKeyResponse(id=api_key.id, name=api_key.name, raw_key=raw_key)
    async def list_api_keys(self, *, tenant_id: UUID) -> list[APIKey]:
        statement = select(APIKey).where(APIKey.tenant_id == tenant_id).order_by(APIKey.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())
