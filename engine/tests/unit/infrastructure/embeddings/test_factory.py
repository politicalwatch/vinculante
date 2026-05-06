import pytest

import vinculante.infrastructure.embeddings.factory as factory_module
from vinculante.infrastructure.config.settings import Settings
from vinculante.infrastructure.embeddings.factory import create_embedder_from_env


def _settings(**overrides) -> Settings:
    base = dict(
        db_url="postgresql+psycopg2://x:x@localhost/x",
        cache_redis_host="redis://localhost",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
    )
    return Settings(**{**base, **overrides})


class _RecordingEmbedder:
    received: Settings | None = None

    def __init__(self, settings: Settings) -> None:
        _RecordingEmbedder.received = settings


def test_create_embedder_uses_embedding_provider(monkeypatch):
    monkeypatch.setitem(factory_module._PROVIDERS, "google", _RecordingEmbedder)
    s = _settings(embedding_provider="google", embedding_model="embedding-001")
    create_embedder_from_env(s)
    assert _RecordingEmbedder.received.embedding_provider == "google"
    assert _RecordingEmbedder.received.embedding_model == "embedding-001"


def test_create_embedder_unknown_provider_raises():
    s = _settings(embedding_provider="unknown_xyz")
    with pytest.raises(ValueError, match="unknown_xyz"):
        create_embedder_from_env(s)
