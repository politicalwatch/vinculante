from langchain_core.language_models.chat_models import BaseChatModel

from vinculante.infrastructure.config.settings import Settings

_PROVIDERS: dict[str, type] = {}


def _register(name: str):
    def decorator(cls):
        _PROVIDERS[name] = cls
        return cls
    return decorator


def create_llm_from_env(settings: Settings | None = None) -> BaseChatModel:
    from vinculante.infrastructure.config.settings import get_settings
    s = settings or get_settings()
    provider = s.llm_provider.lower()
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider!r}. Valid: {list(_PROVIDERS)}")
    return _PROVIDERS[provider](s)


def create_report_llm_from_env(settings: Settings | None = None) -> BaseChatModel:
    """Create LLM for report ingestion, with optional provider/model/temperature overrides."""
    from vinculante.infrastructure.config.settings import get_settings
    s = settings or get_settings()
    provider = (s.report_llm_provider or s.llm_provider).lower()
    model = s.report_llm_model or s.llm_model
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown report LLM provider: {provider!r}. Valid: {list(_PROVIDERS)}")
    overridden = s.model_copy(update={
        "llm_provider": provider,
        "llm_model": model,
        "llm_temperature": s.report_temperature,
    })
    return _PROVIDERS[provider](overridden)


def create_summary_llm_from_env(settings: Settings | None = None) -> BaseChatModel:
    """Create LLM for summary generation, with optional provider/model overrides."""
    from vinculante.infrastructure.config.settings import get_settings
    s = settings or get_settings()
    provider = (s.summary_llm_provider or s.llm_provider).lower()
    model = s.summary_llm_model or s.llm_model
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown summary LLM provider: {provider!r}. Valid: {list(_PROVIDERS)}")
    overridden = s.model_copy(update={
        "llm_provider": provider,
        "llm_model": model,
        "llm_temperature": s.summary_temperature,
    })
    return _PROVIDERS[provider](overridden)


# Import providers to trigger registration
from vinculante.infrastructure.llm import (  # noqa: E402, F401
    anthropic,
    google,
    mistral,
    ollama,
    openai,
)
