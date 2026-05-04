from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_db_session, require_roles, resolve_tenant_context
from app.schemas.lead import LeadResponse
from app.services.lead_service import LeadService

router = APIRouter()


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session=Depends(get_db_session),
):
    leads = await LeadService(session).list_leads(UUID(tenant.tenant_id))
    return [
        LeadResponse(
            id=lead.id,
            session_id=lead.session_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            tag=lead.tag,
            created_at=lead.created_at,
        )
        for lead in leads
    ]
