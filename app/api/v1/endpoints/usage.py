from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_db_session, require_roles, resolve_tenant_context
from app.schemas.usage import UsageSummaryResponse
from app.services.usage_service import UsageService

router = APIRouter()


@router.get(
    "/summary",
    response_model=UsageSummaryResponse,
    summary="Usage summary",
    description="Aggregated tokens, cost, and event counts for the tenant.",
)
async def summary(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session=Depends(get_db_session),
):
    payload = await UsageService(session).summary(UUID(tenant.tenant_id))
    return UsageSummaryResponse(**payload)
