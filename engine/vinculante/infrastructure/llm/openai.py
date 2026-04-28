from langchain_openai import ChatOpenAI

from vinculante.infrastructure.config.settings import Settings

from .factory import _register


@_register("openai")
def create(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
    )
