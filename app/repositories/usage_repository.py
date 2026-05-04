from uuid import UUID

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UsageEvent


class UsageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, event: UsageEvent) -> None:
        self.session.add(event)
        await self.session.flush()

    async def summary(self, tenant_id: UUID) -> dict[str, float | int]:
        statement = select(
            func.count(UsageEvent.id),
            func.coalesce(func.sum(UsageEvent.prompt_tokens), 0),
            func.coalesce(func.sum(UsageEvent.completion_tokens), 0),
            func.coalesce(func.sum(UsageEvent.cost_usd), 0),
            func.coalesce(func.sum(cast(UsageEvent.cache_hit, Integer)), 0),
        ).where(UsageEvent.tenant_id == tenant_id)
        result = await self.session.execute(statement)
        total_requests, prompt_tokens, completion_tokens, total_cost, cache_hits = result.one()
        return {
            "total_requests": int(total_requests or 0),
            "prompt_tokens": int(prompt_tokens or 0),
            "completion_tokens": int(completion_tokens or 0),
            "total_cost_usd": float(total_cost or 0),
            "cache_hits": int(cache_hits or 0),
        }
