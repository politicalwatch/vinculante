from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    db_url: str

    # Cache
    cache_redis_host: str

    # LLM
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.0
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    mistral_api_key: str = ""
    ollama_base_url: str = "http://host.docker.internal:11434"

    # Embeddings
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Matching
    matching_top_k_pct: float = 0.10
    matching_top_k_min: int = 5
    matching_top_k_max: int = 20
    matching_confidence_threshold: float = 0.5
    matching_concurrency: int = 4
    matching_strategy: Literal[
        "one-to-one", "one-to-many", "pipeline", "one-to-many-critic"
    ] = "one-to-one"
    matching_prompt_version: str = "v5"
    matching_critic_prompt_version: str = "v2"

    # Report ingestion
    report_llm_provider: str = ""
    report_llm_model: str = ""
    report_temperature: float | None = None

    # Summary
    summary_llm_provider: str = ""
    summary_llm_model: str = ""
    summary_temperature: float = 0.3
    summary_prompt_version: str = "v1"



@lru_cache
def get_settings() -> Settings:
    return Settings()
