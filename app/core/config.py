from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Botmind AI Backend"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] = ["*"]

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/botmind",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    jwt_secret_key: str = Field(
        default="replace-me-with-a-32-character-minimum-secret",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4.1-mini"
    embedding_dimensions: int = Field(
        default=768,
        alias="EMBEDDING_DIMENSIONS",
        description="Vector size for pgvector column; must match your embedding model (768 nomic-embed-text, 1536 text-embedding-ada-002, etc.)",
    )

    # Ollama settings
    ollama_base_url: str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")
    ollama_timeout_seconds: int = Field(default=120, alias="OLLAMA_TIMEOUT_SECONDS")
    ollama_openai_fallback: bool = Field(default=True, alias="OLLAMA_OPENAI_FALLBACK")
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")  # "ollama" or "openai"

    redis_memory_ttl_seconds: int = 60 * 60 * 24
    redis_cache_ttl_seconds: int = 60 * 10
    session_ttl_seconds: int = 60 * 60 * 24

    rag_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 120

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    webhook_timeout_seconds: int = 10

    @model_validator(mode="after")
    def align_embedding_dimensions_with_ollama_model(self) -> "Settings":
        """Ollama embed models have fixed widths; env/defaults are often wrong (e.g. 1536 vs 768)."""
        if self.llm_provider.lower() != "ollama":
            return self
        dims_by_model: dict[str, int] = {
            "nomic-embed-text": 768,
            "nomic-embed-text:latest": 768,
            "mxbai-embed-large": 1024,
            "mxbai-embed-large:latest": 1024,
            "snowflake-arctic-embed": 1024,
            "snowflake-arctic-embed:latest": 1024,
            "all-minilm": 384,
            "all-minilm:latest": 384,
        }
        key = self.ollama_embed_model.strip()
        if key in dims_by_model:
            object.__setattr__(self, "embedding_dimensions", dims_by_model[key])
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
