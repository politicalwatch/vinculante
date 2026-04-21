from langchain_openai import OpenAIEmbeddings

from vinculante.infrastructure.config.settings import Settings
from .factory import _register


@_register("openai")
def create(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
