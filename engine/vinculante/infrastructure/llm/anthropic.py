from langchain_anthropic import ChatAnthropic

from vinculante.infrastructure.config.settings import Settings
from .factory import _register


@_register("anthropic")
def create(settings: Settings) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
    )
