import logging
from unittest.mock import MagicMock

import pytest

from vinculante.application.ingestion.proposal_ingestor import (
    ProposalIngestor,
    format_authors,
    normalize_author_type,
    parse_authors,
)


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


# ---------------------------------------------------------------------------
# authors
# ---------------------------------------------------------------------------


def test_parse_authors_splits_on_semicolon_and_strips():
    assert parse_authors(" Talento para el Futuro; Harmon ;Political Watch ") == [
        "Talento para el Futuro",
        "Harmon",
        "Political Watch",
    ]


def test_parse_authors_keeps_commas_inside_a_name():
    assert parse_authors("Fundación X, Delegación Madrid; Harmon") == [
        "Fundación X, Delegación Madrid",
        "Harmon",
    ]


def test_parse_authors_drops_empties_and_repeats():
    assert parse_authors("A;; A ; B;") == ["A", "B"]


@pytest.mark.parametrize("value", [None, "", "  ", []])
def test_parse_authors_empty_values(value):
    assert parse_authors(value) == []


def test_parse_authors_accepts_lists():
    assert parse_authors([" Ana Pérez (Fundación X) ", "", "Ana Pérez (Fundación X)"]) == [
        "Ana Pérez (Fundación X)"
    ]


def test_format_authors_round_trips():
    authors = ["Ana Pérez (Fundación X)", "Luis Gil (Universidad Y)"]
    assert parse_authors(format_authors(authors)) == authors


def test_ingest_reads_authors_from_author_column():
    ingestor = _make_ingestor([{"text": "Propuesta", "author": "Harmon; Political Watch"}])
    proposals = ingestor.ingest("file.csv")
    assert proposals[0].authors == ["Harmon", "Political Watch"]


def test_ingest_reads_authors_list_from_report_rows():
    ingestor = _make_ingestor([{"text": "Propuesta", "authors": ["Harmon", "Political Watch"]}])
    proposals = ingestor.ingest("file.pdf")
    assert proposals[0].authors == ["Harmon", "Political Watch"]


def test_ingest_without_author_gives_empty_list():
    ingestor = _make_ingestor([{"text": "Propuesta"}])
    proposals = ingestor.ingest("file.csv")
    assert proposals[0].authors == []
