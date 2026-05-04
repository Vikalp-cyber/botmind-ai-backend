"""
LLM provider factory — returns the correct client based on LLM_PROVIDER config.

Usage:
    from app.integrations.llm import get_llm_client
    client = get_llm_client()
    answer = await client.answer_question(...)
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_llm_client():
    """Return the configured LLM client (Ollama or OpenAI).

    Both clients expose the same interface:
      - embed_texts(texts) -> list[list[float]]
      - answer_question(question, context_blocks, memory_blocks) -> LLMAnswer
      - extract_lead(transcript) -> dict
    """
    settings = get_settings()

    if settings.llm_provider == "ollama":
        from app.integrations.ollama_client import OllamaClient
        logger.info("Using Ollama LLM provider (model=%s, url=%s)", settings.ollama_model, settings.ollama_base_url)
        return OllamaClient()
    else:
        from app.integrations.openai_client import OpenAIClient
        logger.info("Using OpenAI LLM provider (model=%s)", settings.openai_chat_model)
        return OpenAIClient()
