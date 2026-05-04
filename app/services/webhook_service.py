import json
import hashlib
import hmac
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.webhook_repository import WebhookRepository


class WebhookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = WebhookRepository(session)
        self.settings = get_settings()

    async def create_endpoint(self, *, tenant_id: UUID, provider: str, url: str, secret: str | None):
        endpoint = await self.repository.create(
            tenant_id=tenant_id,
            provider=provider,
            url=url,
            secret=secret,
        )
        await self.session.commit()
        return endpoint

    async def list_endpoints(self, tenant_id: UUID):
        return await self.repository.list_active(tenant_id)

    async def dispatch(self, *, tenant_id: UUID, event: str, payload: dict[str, Any]) -> None:
        endpoints = await self.repository.list_active(tenant_id)
        timeout = httpx.Timeout(self.settings.webhook_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for endpoint in endpoints:
                body = {"event": event, "provider": endpoint.provider, "payload": payload}
                headers = {"Content-Type": "application/json"}
                if endpoint.secret:
                    digest = hmac.new(
                        endpoint.secret.encode("utf-8"),
                        json.dumps(body, sort_keys=True).encode("utf-8"),
                        hashlib.sha256,
                    ).hexdigest()
                    headers["X-Botmind-Signature"] = digest
                try:
                    await client.post(endpoint.url, json=body, headers=headers)
                except httpx.HTTPError:
                    continue
