from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_roles, resolve_tenant_context
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from app.schemas.common import APIKeyResponse
from app.services.auth_service import AuthService

router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    name: str


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=201,
    summary="Register tenant and first admin",
    description="Creates a tenant, admin user, and returns JWT access token.",
)
async def signup(payload: SignupRequest, session: AsyncSession = Depends(get_db_session)):
    return await AuthService(session).signup(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Returns JWT for subsequent `Authorization: Bearer` requests.",
)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    return await AuthService(session).login(payload)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current user",
    description="Profile for the authenticated JWT subject.",
)
async def me(user=Depends(get_current_user)):
    return UserResponse.from_model(user)


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    status_code=201,
    summary="Create widget API key",
    description="Admin only. Returns the raw key once; store it securely for `X-API-Key` on chat.",
)
async def create_api_key(
    payload: APIKeyCreateRequest,
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_db_session),
):
    return await AuthService(session).create_api_key(
        tenant_id=user.tenant_id,
        name=payload.name,
    )
@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    summary="List API keys",
    description="Admin only. Key material is never returned after creation.",
)
async def list_api_keys(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_db_session),
):
    records = await AuthService(session).list_api_keys(tenant_id=user.tenant_id)
    return [
        APIKeyResponse(id=record.id, name=record.name, raw_key=None)
        for record in records
    ]
