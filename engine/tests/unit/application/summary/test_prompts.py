import pytest

from vinculante.application.summary.prompts import get_prompt

_ALL_NODES = ("document_overview", "themes", "highlights", "gaps", "synthesize")


def test_get_prompt_document_overview_returns_string_with_placeholders():
    prompt = get_prompt("document_overview")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "{title}" in prompt
    assert "{sections_block}" in prompt


def test_get_prompt_all_nodes_resolve_under_v1():
    for node in _ALL_NODES:
        p = get_prompt(node, "v1")
        assert isinstance(p, str) and len(p) > 0


def test_get_prompt_unknown_version_raises():
    with pytest.raises(ValueError, match="v999"):
        get_prompt("document_overview", "v999")


def test_get_prompt_unknown_node_raises():
    with pytest.raises(ValueError, match="nope"):
        get_prompt("nope")
