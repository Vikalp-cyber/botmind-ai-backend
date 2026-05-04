import json
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import MessageRole
from app.db.session import get_redis
from app.integrations.llm import get_llm_client
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.lead_service import LeadService
from app.services.rag_service import RagService
from app.services.usage_service import UsageService
from app.services.webhook_service import WebhookService
from app.utils.hashing import stable_hash


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.chat_repository = ChatRepository(session)
        self.rag_service = RagService(session)
        self.lead_service = LeadService(session)
        self.usage_service = UsageService(session)
        self.webhook_service = WebhookService(session)
        self.llm = get_llm_client()

    async def chat(self, payload: ChatRequest) -> ChatResponse:
        tenant_id = payload.tenant_id
        redis = get_redis()
        session = await self.chat_repository.get_or_create_session(tenant_id, payload.session_id)
        await self.chat_repository.add_message(
            tenant_id=tenant_id,
            session_id=session.id,
            role=MessageRole.USER,
            content=payload.message,
        )

        cache_key = f"cache:chat:{tenant_id}:{stable_hash(payload.message)}"
        memory_key = f"memory:chat:{tenant_id}:{payload.session_id}"
        active_session_key = f"active:session:{tenant_id}:{payload.session_id}"

        cached_payload = await redis.get(cache_key)
        citations = []
        prompt_tokens = 0
        completion_tokens = 0
        model = None
        started_at = time.perf_counter()

        if cached_payload:
            parsed = json.loads(cached_payload)
            answer_text = parsed["response"]
            citations = [citation.model_validate(item) for item in parsed.get("citations", [])]
            cached = True
        else:
            citations, context_blocks = await self.rag_service.retrieve(
                tenant_id=tenant_id,
                query=payload.message,
            )
            memory_blocks = await redis.lrange(memory_key, 0, 5)
            answer = await self.llm.answer_question(
                question=payload.message,
                context_blocks=context_blocks,
                memory_blocks=memory_blocks,
            )
            answer_text = answer.text
            prompt_tokens = answer.prompt_tokens
            completion_tokens = answer.completion_tokens
            model = answer.model
            cached = False
            await redis.set(
                cache_key,
                json.dumps(
                    {
                        "response": answer_text,
                        "citations": [citation.model_dump(mode="json") for citation in citations],
                    }
                ),
                ex=self.settings.redis_cache_ttl_seconds,
            )

        await self.chat_repository.add_message(
            tenant_id=tenant_id,
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=answer_text,
            cached_response=cached,
            meta={"citations": [citation.model_dump() for citation in citations]},
        )

        await redis.lpush(memory_key, f"user: {payload.message}", f"assistant: {answer_text}")
        await redis.ltrim(memory_key, 0, 11)
        await redis.expire(memory_key, self.settings.redis_memory_ttl_seconds)
        await redis.set(
            active_session_key,
            json.dumps({"session_id": payload.session_id, "tenant_id": str(tenant_id)}),
            ex=self.settings.session_ttl_seconds,
        )

        transcript = f"{payload.message}\n{answer_text}"
        lead = await self.lead_service.capture_from_transcript(
            tenant_id=tenant_id,
            session_id=session.id,
            transcript=transcript,
        )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        await self.usage_service.record_chat_event(
            tenant_id=tenant_id,
            session_id=session.id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_hit=cached,
            latency_ms=latency_ms,
        )
        await self.session.commit()
        if lead is not None:
            await self.webhook_service.dispatch(
                tenant_id=tenant_id,
                event="lead.captured",
                payload={
                    "lead_id": str(lead.id),
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "tag": str(lead.tag),
                },
            )

        return ChatResponse(
            response=answer_text,
            session_id=payload.session_id,
            tenant_id=tenant_id,
            cached=cached,
            citations=citations,
            lead_captured=lead is not None,
        )
