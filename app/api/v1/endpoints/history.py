from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db_session, require_roles, resolve_tenant_context
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import MessageResponse, SessionResponse

router = APIRouter()


@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    summary="List chat sessions",
    description="Tenant-scoped sessions for admin or member.",
)
async def list_sessions(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session=Depends(get_db_session),
):
    records = await ChatRepository(session).list_sessions(UUID(tenant.tenant_id))
    return [
        SessionResponse(
            id=record.id,
            external_id=record.external_id,
            channel=record.channel,
            created_at=record.created_at,
            last_activity_at=record.last_activity_at,
        )
        for record in records
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=list[MessageResponse],
    summary="Get session messages",
    description="Messages for a session UUID. **404** if the session does not belong to the tenant.",
)
async def get_session_messages(
    session_id: str,
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session=Depends(get_db_session),
):
    messages = await ChatRepository(session).list_messages(UUID(tenant.tenant_id), UUID(session_id))
    if not messages:
        # Check if the session exists but just has no messages
        records = await ChatRepository(session).list_sessions(UUID(tenant.tenant_id))
        if not any(str(r.id) == session_id for r in records):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return [
        MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        for message in messages
    ]
