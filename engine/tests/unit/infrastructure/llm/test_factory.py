import pytest

import vinculante.infrastructure.llm.factory as factory_module
from vinculante.infrastructure.config.settings import Settings
from vinculante.infrastructure.llm.factory import create_llm_from_env, create_summary_llm_from_env


def _settings(**overrides) -> Settings:
    base = dict(
        db_url="postgresql+psycopg2://x:x@localhost/x",
        cache_redis_host="redis://localhost",
        llm_provider="openai",
        llm_model="gpt-4",
        llm_temperature=0.5,
        summary_llm_provider="",
        summary_llm_model="",
        summary_temperature=0.3,
    )
    return Settings(**{**base, **overrides})


class _RecordingLLM:
    """Fake provider that records the Settings it received."""
    received: Settings | None = None

    def __init__(self, settings: Settings) -> None:
        _RecordingLLM.received = settings


def test_create_summary_llm_uses_summary_provider_and_model(monkeypatch):
    monkeypatch.setitem(factory_module._PROVIDERS, "anthropic", _RecordingLLM)
    s = _settings(summary_llm_provider="anthropic", summary_llm_model="claude-x", summary_temperature=0.7)
    create_summary_llm_from_env(s)
    assert _RecordingLLM.received.llm_provider == "anthropic"
    assert _RecordingLLM.received.llm_model == "claude-x"
    assert _RecordingLLM.received.llm_temperature == pytest.approx(0.7)


def test_create_summary_llm_falls_back_to_llm_provider_when_summary_blank(monkeypatch):
    monkeypatch.setitem(factory_module._PROVIDERS, "openai", _RecordingLLM)
    s = _settings(summary_llm_provider="", summary_llm_model="")
    create_summary_llm_from_env(s)
    assert _RecordingLLM.received.llm_provider == "openai"
    assert _RecordingLLM.received.llm_model == "gpt-4"


def test_create_summary_llm_temperature_overrides_llm_temperature(monkeypatch):
    monkeypatch.setitem(factory_module._PROVIDERS, "openai", _RecordingLLM)
    s = _settings(llm_temperature=0.9, summary_temperature=0.1)
    create_summary_llm_from_env(s)
    assert _RecordingLLM.received.llm_temperature == pytest.approx(0.1)


def test_create_summary_llm_unknown_provider_raises():
    s = _settings(summary_llm_provider="unknown_xyz")
    with pytest.raises(ValueError, match="unknown_xyz"):
        create_summary_llm_from_env(s)


def test_create_llm_from_env_uses_llm_provider(monkeypatch):
    monkeypatch.setitem(factory_module._PROVIDERS, "anthropic", _RecordingLLM)
    s = _settings(llm_provider="anthropic", llm_model="claude-y", llm_temperature=0.5)
    create_llm_from_env(s)
    assert _RecordingLLM.received.llm_provider == "anthropic"
    assert _RecordingLLM.received.llm_model == "claude-y"
    assert _RecordingLLM.received.llm_temperature == pytest.approx(0.5)
