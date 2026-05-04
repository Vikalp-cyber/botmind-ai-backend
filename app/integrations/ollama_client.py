"""
Ollama LLM client — drop-in replacement for OpenAI chat/generation.

Uses the Ollama REST API at /api/generate (non-streaming) and
/api/generate with stream=true (streaming).
Embeddings are handled via /api/embed.

Falls back to OpenAI when Ollama is unreachable and a valid OpenAI key exists.
"""

import json
import logging
import random
from dataclasses import dataclass, field

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LLMAnswer:
    """Unified response from any LLM provider."""
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str | None = None


class OllamaClient:
    """Production-ready Ollama client with timeout handling, logging,
    and optional OpenAI fallback."""

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.embed_model = settings.ollama_embed_model
        self.timeout = settings.ollama_timeout_seconds
        self.fallback_enabled = settings.ollama_openai_fallback and bool(settings.openai_api_key)

        # Lazy-loaded fallback client
        self._openai_fallback = None

    # ── helpers ───────────────────────────────────────────────────────

    def _get_openai_fallback(self):
        """Lazily create the OpenAI fallback client only when needed."""
        if self._openai_fallback is None:
            from app.integrations.openai_client import OpenAIClient
            self._openai_fallback = OpenAIClient()
        return self._openai_fallback

    async def _is_ollama_available(self) -> bool:
        """Quick health-check against the Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    # ── embeddings ───────────────────────────────────────────────────

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Ollama /api/embed endpoint.
        Falls back to OpenAI or mock vectors on failure."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                results = []
                for text in texts:
                    resp = await client.post(
                        f"{self.base_url}/api/embed",
                        json={"model": self.embed_model, "input": text},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    # Ollama returns {"embeddings": [[...]]}
                    embeddings = data.get("embeddings", [])
                    if embeddings:
                        results.append(embeddings[0])
                    else:
                        raise ValueError("Ollama returned empty embeddings")
                return results

        except Exception as e:
            logger.warning("Ollama embed_texts failed: %s", e)

            # Fallback → OpenAI
            if self.fallback_enabled:
                logger.info("Falling back to OpenAI for embeddings")
                return await self._get_openai_fallback().embed_texts(texts)

            # Dev fallback → mock vectors
            if settings.environment == "development":
                logger.warning("Using MOCK embeddings for development")
                return [
                    [random.uniform(-0.1, 0.1) for _ in range(settings.embedding_dimensions)]
                    for _ in texts
                ]
            raise

    # ── chat / answer ────────────────────────────────────────────────

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    async def answer_question(
        self,
        *,
        question: str,
        context_blocks: list[str],
        memory_blocks: list[str],
    ) -> LLMAnswer:
        """Send a question to Ollama /api/generate (non-streaming)."""
        context_text = "\n\n".join(
            f"[Context {idx + 1}]\n{block}"
            for idx, block in enumerate(context_blocks)
        )
        memory_text = "\n".join(memory_blocks) if memory_blocks else "No prior memory."

        system_prompt = (
            "You are a helpful SaaS support assistant. Answer using the provided context when relevant. "
            "If the answer is not in the context, say so plainly and avoid fabricating details."
        )

        prompt = (
            f"Conversation memory:\n{memory_text}\n\n"
            f"Knowledge base context:\n{context_text or 'No context found.'}\n\n"
            f"User question:\n{question}"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            response_text = data.get("response", "").strip()
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)

            logger.info(
                "Ollama answer: model=%s prompt_tokens=%d completion_tokens=%d",
                self.model, prompt_eval_count, eval_count,
            )

            return LLMAnswer(
                text=response_text,
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                model=data.get("model", self.model),
            )

        except Exception as e:
            logger.error("Ollama answer_question failed: %s", e)

            # Fallback → OpenAI
            if self.fallback_enabled:
                logger.info("Falling back to OpenAI for chat")
                return await self._get_openai_fallback().answer_question(
                    question=question,
                    context_blocks=context_blocks,
                    memory_blocks=memory_blocks,
                )

            # Dev fallback → mock answer
            if settings.environment == "development":
                logger.warning("Using MOCK answer for development")
                return LLMAnswer(
                    text=(
                        "[MOCK – Ollama unreachable] I cannot answer right now. "
                        "Please ensure Ollama is running on the configured host."
                    ),
                    model="mock-model",
                )
            raise

    # ── streaming answer ─────────────────────────────────────────────

    async def answer_question_stream(
        self,
        *,
        question: str,
        context_blocks: list[str],
        memory_blocks: list[str],
    ):
        """Yield response tokens one-by-one via Ollama streaming.

        Yields dicts: {"token": str, "done": bool}
        """
        context_text = "\n\n".join(
            f"[Context {idx + 1}]\n{block}"
            for idx, block in enumerate(context_blocks)
        )
        memory_text = "\n".join(memory_blocks) if memory_blocks else "No prior memory."

        system_prompt = (
            "You are a helpful SaaS support assistant. Answer using the provided context when relevant. "
            "If the answer is not in the context, say so plainly and avoid fabricating details."
        )

        prompt = (
            f"Conversation memory:\n{memory_text}\n\n"
            f"Knowledge base context:\n{context_text or 'No context found.'}\n\n"
            f"User question:\n{question}"
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=10)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": prompt,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    yield {
                        "token": chunk.get("response", ""),
                        "done": chunk.get("done", False),
                    }

    # ── lead extraction ──────────────────────────────────────────────

    async def extract_lead(self, transcript: str) -> dict[str, str | None]:
        """Extract lead fields from a chat transcript."""
        system_prompt = (
            "Extract lead fields from the transcript. Return ONLY strict JSON with keys "
            "name, email, phone. Use null for missing values. No extra text."
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": transcript,
                        "stream": False,
                        "format": "json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            return json.loads(data.get("response", "{}"))

        except Exception as e:
            logger.error("Ollama extract_lead failed: %s", e)

            # Fallback → OpenAI
            if self.fallback_enabled:
                logger.info("Falling back to OpenAI for lead extraction")
                return await self._get_openai_fallback().extract_lead(transcript)

            # Dev fallback
            if settings.environment == "development":
                return {"name": None, "email": None, "phone": None}

            return {"name": None, "email": None, "phone": None}
