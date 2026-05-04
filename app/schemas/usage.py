from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    total_requests: int
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float
    cache_hits: int
