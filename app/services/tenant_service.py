from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tenant, TenantStatus


@dataclass
class TenantContext:
    tenant_id: str
    principal_id: str | None
    api_key_id: str | None = None


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_context(self, tenant_id: str, principal_id: str | None) -> TenantContext:
        tenant_uuid = UUID(tenant_id)
        tenant = await self.session.scalar(select(Tenant).where(Tenant.id == tenant_uuid))
        if tenant is None or tenant.status != TenantStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        await self.session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": str(tenant_uuid)},
        )
        return TenantContext(tenant_id=str(tenant_uuid), principal_id=principal_id)
