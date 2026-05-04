from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_principal, get_db_session, resolve_tenant_context
from app.core.rate_limit import RateLimiter
from app.core.security import decode_token, verify_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.tenant_service import TenantService

router = APIRouter()


async def _authorize_chat(
    *,
    payload: ChatRequest,
    session: AsyncSession,
    authorization: str | None,
    x_api_key: str | None,
) -> None:
    tenant_service = TenantService(session)
    if authorization:
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
        token = authorization.split(" ", 1)[1]
        principal = decode_token(token)
        if principal.tenant_id != str(payload.tenant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
        await tenant_service.set_context(principal.tenant_id, principal.sub)
        await RateLimiter().enforce(tenant_id=principal.tenant_id, subject=principal.sub)
        return

    if x_api_key:
        api_key = await verify_api_key(session, tenant_id=payload.tenant_id, raw_key=x_api_key)
        if api_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        await tenant_service.set_context(str(payload.tenant_id), None)
        await RateLimiter().enforce(tenant_id=str(payload.tenant_id), subject=str(api_key.id))
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    await _authorize_chat(
        payload=payload,
        session=session,
        authorization=authorization,
        x_api_key=x_api_key,
    )
    return await ChatService(session).chat(payload)


@router.websocket("/ws/chat/{tenant_id}/{session_id}")
async def websocket_chat(websocket: WebSocket, tenant_id: UUID, session_id: str):
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    principal = decode_token(token)
    if principal.tenant_id != str(tenant_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    async for session in get_db_session():
        await TenantService(session).set_context(principal.tenant_id, principal.sub)
        limiter = RateLimiter()
        try:
            while True:
                text = await websocket.receive_text()
                await limiter.enforce(tenant_id=principal.tenant_id, subject=principal.sub)
                response = await ChatService(session).chat(
                    ChatRequest(message=text, session_id=session_id, tenant_id=tenant_id)
                )
                await websocket.send_json(response.model_dump(mode="json"))
        except WebSocketDisconnect:
            return
