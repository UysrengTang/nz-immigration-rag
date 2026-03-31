from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NZ Immigration RAG"
    app_version: str = "0.1.0"
    app_env: str = "development"

    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    database_url: str | None = None
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    ingestion_user_agent: str = "nz-immigration-rag/0.1 (+official-source-loader)"
    http_timeout_seconds: int = Field(default=30, ge=1, le=120)
    chunk_size_tokens: int = Field(default=350, ge=50, le=2000)
    chunk_overlap_tokens: int = Field(default=40, ge=0, le=500)
    vector_top_k: int = Field(default=12, ge=1, le=100)
    retrieval_top_n: int = Field(default=6, ge=1, le=50)
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "nz-immigration-rag"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
