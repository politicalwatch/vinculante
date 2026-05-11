import logging
from unittest.mock import MagicMock

import pytest

from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor, normalize_author_type


# ---------------------------------------------------------------------------
# author_type fallback behaviour
# ---------------------------------------------------------------------------


def _make_ingestor(rows: list[dict]) -> ProposalIngestor:
    loader = MagicMock()
    loader.load.return_value = rows
    repo = MagicMock()
    repo.bulk_save.side_effect = lambda proposals: proposals
    return ProposalIngestor(repo=repo, loader=loader)


def test_author_type_row_value_wins_over_cli_default():
    ingestor = _make_ingestor([{"text": "Propuesta A", "author_type": "citizen"}])
    proposals = ingestor.ingest("file.csv", author_type="academia")
    assert proposals[0].author_type == "citizen"


def test_author_type_cli_default_used_when_row_missing():
    ingestor = _make_ingestor([{"text": "Propuesta B"}])
    proposals = ingestor.ingest("file.csv", author_type="citizen")
    assert proposals[0].author_type == "citizen"

# ---------------------------------------------------------------------------
# normalize_author_type
# ---------------------------------------------------------------------------


def test_normalize_canonical_citizen():
    assert normalize_author_type("citizen") == "citizen"


def test_normalize_canonical_academia():
    assert normalize_author_type("academia") == "academia"


def test_normalize_canonical_institution():
    assert normalize_author_type("institution") == "institution"


def test_normalize_canonical_government():
    assert normalize_author_type("government") == "government"


def test_normalize_canonical_ngo():
    assert normalize_author_type("ngo") == "ngo"


def test_normalize_none_returns_none():
    assert normalize_author_type(None) is None


def test_normalize_empty_string_returns_none():
    assert normalize_author_type("") is None


def test_normalize_strips_and_lowercases():
    assert normalize_author_type("  CITIZEN  ") == "citizen"
    assert normalize_author_type("Academia") == "academia"


def test_normalize_unknown_returns_none_and_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="vinculante.application.ingestion.proposal_ingestor"):
        result = normalize_author_type("unknownvalue")
    assert result is None
    assert "unknownvalue" in caplog.text


@pytest.mark.parametrize("value", ["citizen", "academia", "institution", "government", "ngo"])
def test_normalize_all_canonical_passthrough(value):
    assert normalize_author_type(value) == value
