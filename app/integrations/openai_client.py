import json
from dataclasses import dataclass

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

settings = get_settings()


@dataclass
class LLMAnswer:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str | None = None


class OpenAIClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import random
        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts,
                encoding_format="float",
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            # Check for RateLimitError or InsufficientQuota
            if "insufficient_quota" in str(e).lower() or "rate_limit" in str(e).lower():
                if settings.environment == "development":
                    # Generate deterministic-ish random vectors for development/testing
                    # Dimension must match settings.embedding_dimensions / pgvector column
                    print(f"WARNING: OpenAI Quota exceeded. Using MOCK embeddings for development. Error: {e}")
                    return [[random.uniform(-0.1, 0.1) for _ in range(settings.embedding_dimensions)] for _ in texts]
            raise e

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    async def answer_question(
        self,
        *,
        question: str,
        context_blocks: list[str],
        memory_blocks: list[str],
    ) -> LLMAnswer:
        context_text = "\n\n".join(f"[Context {idx + 1}]\n{block}" for idx, block in enumerate(context_blocks))
        memory_text = "\n".join(memory_blocks) if memory_blocks else "No prior memory."
        try:
            response = await self.client.responses.create(
                model=settings.openai_chat_model,
                instructions=(
                    "You are a helpful SaaS support assistant. Answer using the provided context when relevant. "
                    "If the answer is not in the context, say so plainly and avoid fabricating details."
                ),
                input=(
                    f"Conversation memory:\n{memory_text}\n\n"
                    f"Knowledge base context:\n{context_text or 'No context found.'}\n\n"
                    f"User question:\n{question}"
                ),
            )
            usage = getattr(response, "usage", None)
            return LLMAnswer(
                text=(response.output_text or "").strip(),
                prompt_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
                completion_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
                model=getattr(response, "model", settings.openai_chat_model),
            )
        except Exception as e:
            if ("insufficient_quota" in str(e).lower() or "rate_limit" in str(e).lower()) and settings.environment == "development":
                print(f"WARNING: OpenAI Quota exceeded. Using MOCK answer for development. Error: {e}")
                return LLMAnswer(
                    text="[MOCK ANSWER] I'm sorry, I cannot answer right now because the OpenAI API quota is exceeded. Please check your billing details.",
                    model="mock-model"
                )
            raise e

    async def extract_lead(self, transcript: str) -> dict[str, str | None]:
        try:
            response = await self.client.responses.create(
                model=settings.openai_chat_model,
                instructions=(
                    "Extract lead fields from the transcript. Return strict JSON with keys "
                    "name, email, phone. Use null for missing values."
                ),
                input=transcript,
            )
            return json.loads(response.output_text or "{}")
        except Exception as e:
            if ("insufficient_quota" in str(e).lower() or "rate_limit" in str(e).lower()) and settings.environment == "development":
                 print(f"WARNING: OpenAI Quota exceeded. Using MOCK lead extraction for development. Error: {e}")
                 return {"name": "Mock User", "email": "mock@example.com", "phone": "555-0199"}
            
            if isinstance(e, (TypeError, json.JSONDecodeError)):
                return {"name": None, "email": None, "phone": None}
            raise e
