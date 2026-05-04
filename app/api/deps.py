from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, verify_api_key
from app.db.session import get_async_session
from app.schemas.auth import TokenPayload
from app.services.auth_service import AuthService
from app.services.tenant_service import TenantContext, TenantService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")
    return decode_token(credentials.credentials)


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    principal: TokenPayload = Depends(get_current_principal),
):
    auth_service = AuthService(session)
    user = await auth_service.get_active_user(UUID(principal.sub), principal.tenant_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str):
    async def dependency(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency


async def resolve_tenant_context(
    session: AsyncSession = Depends(get_db_session),
    principal: TokenPayload = Depends(get_current_principal),
) -> TenantContext:
    tenant_service = TenantService(session)
    return await tenant_service.set_context(principal.tenant_id, principal.sub)


async def resolve_widget_tenant_context(
    tenant_id: UUID,
    x_api_key: str = Header(alias="X-API-Key"),
    session: AsyncSession = Depends(get_db_session),
) -> TenantContext:
    tenant_service = TenantService(session)
    api_key = await verify_api_key(session, tenant_id=tenant_id, raw_key=x_api_key)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    context = await tenant_service.set_context(str(tenant_id), None)
    context.api_key_id = str(api_key.id)
    return context
