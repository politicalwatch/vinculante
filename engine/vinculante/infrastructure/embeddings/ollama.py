from langchain_ollama import OllamaEmbeddings

from vinculante.infrastructure.config.settings import Settings
from .factory import _register


@_register("ollama")
def create(settings: Settings) -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )
