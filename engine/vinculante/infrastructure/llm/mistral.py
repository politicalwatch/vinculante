from langchain_mistralai import ChatMistralAI

from vinculante.infrastructure.config.settings import Settings

from .factory import _register


@_register("mistral")
def create(settings: Settings) -> ChatMistralAI:
    return ChatMistralAI(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=settings.llm_temperature,
    )
