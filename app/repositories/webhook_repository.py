from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WebhookEndpoint


class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        tenant_id: UUID,
        provider: str,
        url: str,
        secret: str | None,
    ) -> WebhookEndpoint:
        endpoint = WebhookEndpoint(
            tenant_id=tenant_id,
            provider=provider,
            url=url,
            secret=secret,
        )
        self.session.add(endpoint)
        await self.session.flush()
        return endpoint

    async def list_active(self, tenant_id: UUID) -> list[WebhookEndpoint]:
        result = await self.session.execute(
            select(WebhookEndpoint).where(
                WebhookEndpoint.tenant_id == tenant_id,
                WebhookEndpoint.is_active.is_(True),
            )
        )
        return list(result.scalars().all())
