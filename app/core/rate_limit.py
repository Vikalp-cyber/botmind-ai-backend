from fastapi import HTTPException, status

from app.core.config import get_settings
from app.db.session import get_redis


class RateLimiter:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def enforce(self, *, tenant_id: str, subject: str) -> None:
        redis = get_redis()
        key = f"rate:{tenant_id}:{subject}"
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.settings.rate_limit_window_seconds)
        if current > self.settings.rate_limit_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
