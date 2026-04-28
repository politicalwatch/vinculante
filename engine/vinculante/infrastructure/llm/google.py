from langchain_google_genai import ChatGoogleGenerativeAI

from vinculante.infrastructure.config.settings import Settings

from .factory import _register


@_register("google")
def create(settings: Settings) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
    )
