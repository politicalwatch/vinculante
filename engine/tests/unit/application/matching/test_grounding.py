import pytest

from vinculante.application.matching.grounding import find_quote_offsets, verify_quotes

SECTION = (
    "Artículo 3. Los centros educativos incorporarán orientadores y psicólogos "
    "especializados en bienestar emocional.\n"
    "Asimismo, se promoverá la formación continua del profesorado en detección temprana."
)


# ── find_quote_offsets ────────────────────────────────────────────────────────

def test_verbatim_match_returns_correct_offsets():
    quote = "orientadores y psicólogos"
    offsets = find_quote_offsets(quote, SECTION)
    assert offsets is not None
    start, end = offsets
    assert SECTION[start:end] == "orientadores y psicólogos"


def test_accent_insensitive():
    # quote uses ASCII 'o', section has 'ó'
    offsets = find_quote_offsets("psicologos especializados", SECTION)
    assert offsets is not None
    start, end = offsets
    assert "psicólogos" in SECTION[start:end]


def test_case_insensitive():
    offsets = find_quote_offsets("LOS CENTROS EDUCATIVOS", SECTION)
    assert offsets is not None
    start, end = offsets
    assert SECTION[start:end].lower() == "los centros educativos"


def test_collapsed_whitespace_in_section():
    section = "incorporarán   orientadores\ny\tpsicólogos especializados"
    offsets = find_quote_offsets("orientadores y psicólogos", section)
    assert offsets is not None


def test_surrounding_double_quotes_stripped():
    offsets = find_quote_offsets('"orientadores y psicólogos"', SECTION)
    assert offsets is not None


def test_surrounding_typographic_quotes_stripped():
    offsets = find_quote_offsets("«orientadores y psicólogos»", SECTION)
    assert offsets is not None


def test_leading_ellipsis_stripped():
    offsets = find_quote_offsets("...orientadores y psicólogos", SECTION)
    assert offsets is not None


def test_trailing_unicode_ellipsis_stripped():
    offsets = find_quote_offsets("orientadores y psicólogos…", SECTION)
    assert offsets is not None


def test_quote_not_in_section_returns_none():
    offsets = find_quote_offsets("medidas cautelares urgentes", SECTION)
    assert offsets is None


def test_quote_too_short_returns_none():
    offsets = find_quote_offsets("centros", SECTION)
    assert offsets is None


def test_empty_quote_returns_none():
    assert find_quote_offsets("", SECTION) is None


def test_whitespace_only_quote_returns_none():
    assert find_quote_offsets("   ", SECTION) is None


def test_offsets_are_start_inclusive_end_exclusive():
    quote = "formación continua del profesorado"
    offsets = find_quote_offsets(quote, SECTION)
    assert offsets is not None
    start, end = offsets
    # round-trip: normalized form of slice equals normalized form of quote
    assert SECTION[start:end].replace("ó", "o").lower() == quote.replace("ó", "o").lower()


# ── verify_quotes ─────────────────────────────────────────────────────────────

def test_verify_quotes_returns_all_verified_spans():
    quotes = [
        "orientadores y psicólogos",
        "formación continua del profesorado",
    ]
    spans = verify_quotes(quotes, SECTION)
    assert len(spans) == 2
    for start, end in spans:
        assert 0 <= start < end <= len(SECTION)


def test_verify_quotes_skips_unverified():
    quotes = ["orientadores y psicólogos", "frase que no existe en el texto"]
    spans = verify_quotes(quotes, SECTION)
    assert len(spans) == 1


def test_verify_quotes_empty_input_returns_empty():
    assert verify_quotes([], SECTION) == []


def test_verify_quotes_none_verified_returns_empty():
    assert verify_quotes(["texto inventado completamente"], SECTION) == []
