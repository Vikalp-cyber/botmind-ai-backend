from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UsageEvent
from app.repositories.usage_repository import UsageRepository


class UsageService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UsageRepository(session)

    async def record_chat_event(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        model: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        cache_hit: bool,
        latency_ms: int,
        cost_usd: float = 0,
    ) -> None:
        await self.repository.record(
            UsageEvent(
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="chat.completion",
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cache_hit=cache_hit,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                created_at=datetime.now(UTC),
            )
        )

    async def summary(self, tenant_id: UUID):
        return await self.repository.summary(tenant_id)
