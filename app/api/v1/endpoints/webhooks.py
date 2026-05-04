from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_db_session, require_roles, resolve_tenant_context
from app.schemas.webhook import WebhookEndpointCreate, WebhookEndpointResponse
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.get(
    "/endpoints",
    response_model=list[WebhookEndpointResponse],
    summary="List webhook endpoints",
    description="Configured outbound webhook targets for CRM integrations.",
)
async def list_endpoints(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session=Depends(get_db_session),
):
    endpoints = await WebhookService(session).list_endpoints(UUID(tenant.tenant_id))
    return [
        WebhookEndpointResponse(
            id=endpoint.id,
            provider=endpoint.provider,
            url=endpoint.url,
            is_active=endpoint.is_active,
            created_at=endpoint.created_at,
        )
        for endpoint in endpoints
    ]


@router.post(
    "/endpoints",
    response_model=WebhookEndpointResponse,
    status_code=201,
    summary="Create webhook endpoint",
    description="Admin only. Registers URL (and optional secret) for outbound events.",
)
async def create_endpoint(
    payload: WebhookEndpointCreate,
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session=Depends(get_db_session),
):
    endpoint = await WebhookService(session).create_endpoint(
        tenant_id=UUID(tenant.tenant_id),
        provider=payload.provider,
        url=str(payload.url),
        secret=payload.secret,
    )
    return WebhookEndpointResponse(
        id=endpoint.id,
        provider=endpoint.provider,
        url=endpoint.url,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at,
    )


@router.post(
    "/dispatch-test",
    summary="Send test webhook",
    description="Admin only. Fires a `crm.test` payload to configured endpoints.",
)
async def dispatch_test(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session=Depends(get_db_session),
):
    await WebhookService(session).dispatch(
        tenant_id=UUID(tenant.tenant_id),
        event="crm.test",
        payload={"message": "Botmind webhook connectivity test"},
    )
    return {"status": "sent"}
