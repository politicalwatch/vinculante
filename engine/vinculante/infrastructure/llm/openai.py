from langchain_openai import ChatOpenAI

from vinculante.infrastructure.config.settings import Settings

from .factory import _register


@_register("openai")
def create(settings: Settings) -> ChatOpenAI:
    kwargs = {"model": settings.llm_model, "api_key": settings.openai_api_key}
    if settings.llm_temperature is not None:
        kwargs["temperature"] = settings.llm_temperature
    return ChatOpenAI(**kwargs)
