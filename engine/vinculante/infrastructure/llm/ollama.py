from langchain_ollama import ChatOllama

from vinculante.infrastructure.config.settings import Settings
from .factory import _register


@_register("ollama")
def create(settings: Settings) -> ChatOllama:
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
    )
