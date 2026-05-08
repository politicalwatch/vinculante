from types import SimpleNamespace

from vinculante.application.summary.inputs import (
    _derive_section_title,
    anonymise_author,
    classify_author_type,
    curate_stats,
    find_orphan_sections,
    find_unmatched_proposals_with_ninguno,
    format_curated_stats,
    format_matches_for_highlights,
    format_orphan_sections,
    format_sections_for_overview,
    format_unmatched_proposals,
)

# ---------------------------------------------------------------------------
# Helpers — plain namespaces avoid SQLAlchemy mapper overhead in unit tests
# ---------------------------------------------------------------------------


def _section(
    *,
    id: int = 1,
    text: str = "x" * 150,
    text_markdown: str | None = None,
    is_matchable: bool = True,
    section_number: str | None = None,
    page_number: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        text=text,
        text_markdown=text_markdown,
        is_matchable=is_matchable,
        section_number=section_number,
        page_number=page_number,
    )


def _proposal(
    *,
    id: int = 1,
    text: str = "x" * 90,
    author: str | None = None,
    author_type: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(id=id, text=text, author=author, author_type=author_type)


def _match(
    *,
    proposal_id: int = 1,
    section_id: int = 1,
    degree: str = "alto",
    confidence: float = 0.9,
    explanation: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        proposal_id=proposal_id,
        section_id=section_id,
        degree=degree,
        confidence=confidence,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# classify_author_type
# ---------------------------------------------------------------------------


def test_classify_citizen_canonical():
    assert classify_author_type("citizen") == "citizen"


def test_classify_academia_canonical():
    assert classify_author_type("academia") == "academia"


def test_classify_institution_canonical():
    assert classify_author_type("institution") is None


def test_classify_government_canonical():
    assert classify_author_type("government") is None


def test_classify_ngo_canonical():
    assert classify_author_type("ngo") is None


def test_classify_none_returns_none():
    assert classify_author_type(None) is None


def test_classify_empty_string_returns_none():
    assert classify_author_type("") is None


def test_classify_unknown_returns_none():
    assert classify_author_type("randomvalue") is None


# ---------------------------------------------------------------------------
# anonymise_author
# ---------------------------------------------------------------------------


def test_anonymise_author_citizen():
    assert anonymise_author("Real Name", "citizen") == "propuesta ciudadana"


def test_anonymise_author_none_author_type():
    assert anonymise_author("any", None) == "propuesta ciudadana"


def test_anonymise_author_empty_author_type():
    assert anonymise_author("any", "") == "propuesta ciudadana"


def test_anonymise_author_non_citizen_with_author():
    assert anonymise_author("Univ. Autónoma", "academia") == "Univ. Autónoma"


def test_anonymise_author_non_citizen_without_author():
    assert anonymise_author(None, "academia") == "propuesta ciudadana"


# ---------------------------------------------------------------------------
# _derive_section_title
# ---------------------------------------------------------------------------


def test_derive_section_title_markdown_over_text():
    s = _section(text="plain text first line", text_markdown="## Heading from markdown\nrest")
    assert _derive_section_title(s) == "Heading from markdown"


def test_derive_section_title_strips_leading_hashes():
    s = _section(text="x", text_markdown="### Artículo 5\nbody")
    assert _derive_section_title(s) == "Artículo 5"


def test_derive_section_title_falls_back_to_text():
    s = _section(text="First line from text\nmore", text_markdown=None)
    assert _derive_section_title(s) == "First line from text"


def test_derive_section_title_truncates_at_sentence_boundary():
    long_first_line = "A" * 50 + ". " + "B" * 80
    s = _section(text=long_first_line, text_markdown=None)
    result = _derive_section_title(s)
    assert result == "A" * 50
    assert ". " not in result


def test_derive_section_title_hard_truncates_at_120():
    s = _section(text="Z" * 200, text_markdown=None)
    result = _derive_section_title(s)
    assert result is not None
    assert len(result) <= 120
    assert result.endswith("…")


def test_derive_section_title_returns_none_for_empty():
    s = _section(text="", text_markdown=None)
    assert _derive_section_title(s) is None


def test_derive_section_title_returns_none_for_whitespace():
    s = _section(text="   \n  ", text_markdown=None)
    assert _derive_section_title(s) is None


# ---------------------------------------------------------------------------
# find_orphan_sections
# ---------------------------------------------------------------------------


def test_find_orphan_sections_keeps_qualifying():
    s = _section(id=1, text="a" * 100, is_matchable=True)
    result = find_orphan_sections([s], [])
    assert result == [s]


def test_find_orphan_sections_skips_non_matchable():
    s = _section(id=1, text="a" * 100, is_matchable=False)
    assert find_orphan_sections([s], []) == []


def test_find_orphan_sections_skips_matched():
    s = _section(id=1, text="a" * 100, is_matchable=True)
    m = _match(section_id=1)
    assert find_orphan_sections([s], [m]) == []


def test_find_orphan_sections_skips_text_below_100():
    s = _section(id=1, text="a" * 99, is_matchable=True)
    assert find_orphan_sections([s], []) == []


def test_find_orphan_sections_boundary_exactly_100():
    s = _section(id=1, text="a" * 100, is_matchable=True)
    assert find_orphan_sections([s], []) == [s]


# ---------------------------------------------------------------------------
# find_unmatched_proposals_with_ninguno
# ---------------------------------------------------------------------------


def test_find_unmatched_excludes_accepted_proposals():
    p = _proposal(id=1, text="x" * 90, author_type="citizen")
    m_alto = _match(proposal_id=1, degree="alto")
    result = find_unmatched_proposals_with_ninguno([p], [m_alto])
    assert result == []


def test_find_unmatched_excludes_text_below_80():
    p = _proposal(id=1, text="x" * 79, author_type="citizen")
    assert find_unmatched_proposals_with_ninguno([p], []) == []


def test_find_unmatched_skips_unknown_author_type():
    p = _proposal(id=1, text="x" * 80, author_type="institution")
    assert find_unmatched_proposals_with_ninguno([p], []) == []


def test_find_unmatched_skips_null_author_type():
    p = _proposal(id=1, text="x" * 80, author_type=None)
    assert find_unmatched_proposals_with_ninguno([p], []) == []


def test_find_unmatched_includes_eligible_no_ninguno():
    p = _proposal(id=1, text="x" * 80, author_type="citizen")
    result = find_unmatched_proposals_with_ninguno([p], [])
    assert len(result) == 1
    assert result[0]["proposal"] is p
    assert result[0]["representative_ninguno"] is None


def test_find_unmatched_picks_highest_confidence_ninguno():
    p = _proposal(id=1, text="x" * 80, author_type="citizen")
    m_low = _match(proposal_id=1, degree="ninguno", confidence=0.3, explanation="x" * 35)
    m_high = _match(proposal_id=1, degree="ninguno", confidence=0.8, explanation="y" * 35)
    result = find_unmatched_proposals_with_ninguno([p], [m_low, m_high])
    assert result[0]["representative_ninguno"] == "y" * 35


def test_find_unmatched_skips_ninguno_explanation_below_30():
    p = _proposal(id=1, text="x" * 80, author_type="citizen")
    m = _match(proposal_id=1, degree="ninguno", confidence=0.9, explanation="short")
    result = find_unmatched_proposals_with_ninguno([p], [m])
    assert result[0]["representative_ninguno"] is None


def test_find_unmatched_truncates_ninguno_explanation_to_300():
    p = _proposal(id=1, text="x" * 80, author_type="citizen")
    m = _match(proposal_id=1, degree="ninguno", confidence=0.9, explanation="z" * 400)
    result = find_unmatched_proposals_with_ninguno([p], [m])
    assert result[0]["representative_ninguno"] == "z" * 300


# ---------------------------------------------------------------------------
# curate_stats
# ---------------------------------------------------------------------------


def test_curate_stats_extracts_expected_keys():
    stats = {
        "coverage": {"pct_sections_matched": 0.6, "orphan_sections": 3},
        "distribution": {"avg_matches_per_matched_section": 2.1},
        "degree": {"alto": {"count": 5}, "medio": {"count": 8}},
        "quality": {"top_proposals": [{"proposal_id": 10}, {"proposal_id": 20}]},
    }
    result = curate_stats(stats)
    assert result["pct_sections_matched"] == 0.6
    assert result["orphan_sections_count"] == 3
    assert result["avg_matches_per_matched_section"] == 2.1
    assert result["alto_count"] == 5
    assert result["medio_count"] == 8
    assert result["top_proposal_ids"] == [10, 20]


def test_curate_stats_missing_keys_return_none_or_empty():
    result = curate_stats({})
    assert result["pct_sections_matched"] is None
    assert result["orphan_sections_count"] is None
    assert result["avg_matches_per_matched_section"] is None
    assert result["alto_count"] is None
    assert result["medio_count"] is None
    assert result["top_proposal_ids"] == []


# ---------------------------------------------------------------------------
# format_sections_for_overview
# ---------------------------------------------------------------------------


def test_format_sections_for_overview_uses_section_number():
    s = _section(id=1, text="hello", section_number="3", page_number=None)
    result = format_sections_for_overview([s])
    assert "Sección 3" in result


def test_format_sections_for_overview_fallback_id():
    s = _section(id=7, text="hello", section_number=None, page_number=None)
    result = format_sections_for_overview([s])
    assert "[sección id 7]" in result


def test_format_sections_for_overview_includes_page():
    s = _section(id=1, text="hello", section_number="2", page_number=5)
    result = format_sections_for_overview([s])
    assert "(p. 5)" in result


def test_format_sections_for_overview_truncates_at_800():
    s = _section(id=1, text="a" * 801, section_number="1")
    result = format_sections_for_overview([s])
    assert "a" * 800 + "…" in result


def test_format_sections_for_overview_no_truncation_at_800():
    s = _section(id=1, text="a" * 800, section_number="1")
    result = format_sections_for_overview([s])
    assert "…" not in result


# ---------------------------------------------------------------------------
# format_orphan_sections / format_unmatched_proposals
# ---------------------------------------------------------------------------


def test_format_orphan_sections_empty_returns_ninguna():
    assert format_orphan_sections([]) == "(ninguna)"


def test_format_orphan_sections_non_empty():
    s = _section(id=1, text="orphan text", section_number="4")
    result = format_orphan_sections([s])
    assert "Sección 4" in result
    assert "orphan text" in result


def test_format_unmatched_proposals_empty_returns_ninguna():
    assert format_unmatched_proposals([]) == "(ninguna)"


def test_format_unmatched_proposals_citizen_in_citizen_block():
    p = _proposal(id=1, text="propuesta ciudadana", author_type="citizen")
    item = {"proposal": p, "representative_ninguno": None}
    result = format_unmatched_proposals([item])
    assert "## Propuestas ciudadanas" in result
    assert "propuesta ciudadana" in result
    assert "## Propuestas académicas" not in result


def test_format_unmatched_proposals_academia_in_academia_block():
    p = _proposal(id=1, text="propuesta académica", author="Univ X", author_type="academia")
    item = {"proposal": p, "representative_ninguno": "razón detallada"}
    result = format_unmatched_proposals([item])
    assert "## Propuestas académicas" in result
    assert "propuesta académica" in result
    assert "razón detallada" in result
    assert "## Propuestas ciudadanas" not in result


def test_format_unmatched_proposals_both_groups_show_both_headers():
    pc = _proposal(id=1, text="propuesta ciudadana", author_type="citizen")
    pa = _proposal(id=2, text="propuesta academia", author_type="academia")
    items = [
        {"proposal": pc, "representative_ninguno": None},
        {"proposal": pa, "representative_ninguno": None},
    ]
    result = format_unmatched_proposals(items)
    assert "## Propuestas ciudadanas" in result
    assert "## Propuestas académicas" in result


def test_format_unmatched_proposals_null_author_type_skipped():
    p = _proposal(id=1, text="propuesta sin tipo")
    item = {"proposal": p, "representative_ninguno": None}
    assert format_unmatched_proposals([item]) == "(ninguna)"


def test_format_unmatched_proposals_skips_institution_government_ngo():
    items = [
        {"proposal": _proposal(id=1, text="x" * 50, author_type="institution"), "representative_ninguno": None},
        {"proposal": _proposal(id=2, text="x" * 50, author_type="government"), "representative_ninguno": None},
        {"proposal": _proposal(id=3, text="x" * 50, author_type="ngo"), "representative_ninguno": None},
    ]
    assert format_unmatched_proposals(items) == "(ninguna)"


# ---------------------------------------------------------------------------
# format_matches_for_highlights — split by author_type
# ---------------------------------------------------------------------------


def _highlight_match(
    *,
    proposal_id: int,
    section_id: int = 1,
    degree: str = "alto",
    confidence: float = 0.9,
    explanation: str = "buena explicación",
) -> SimpleNamespace:
    return SimpleNamespace(
        proposal_id=proposal_id,
        section_id=section_id,
        degree=degree,
        confidence=confidence,
        explanation=explanation,
    )


def test_format_matches_for_highlights_citizen_only():
    p = _proposal(id=1, text="propuesta ciudadana", author_type="citizen")
    s = _section(id=1, section_number="3")
    m = _highlight_match(proposal_id=1)
    result = format_matches_for_highlights([m], [s], [p], {1: "propuesta ciudadana"})
    assert "## Propuestas ciudadanas" in result
    assert "## Propuestas académicas" not in result


def test_format_matches_for_highlights_academia_only():
    p = _proposal(id=1, text="propuesta academia", author="Univ X", author_type="academia")
    s = _section(id=1, section_number="2")
    m = _highlight_match(proposal_id=1)
    result = format_matches_for_highlights([m], [s], [p], {1: "Univ X"})
    assert "## Propuestas académicas" in result
    assert "## Propuestas ciudadanas" not in result


def test_format_matches_for_highlights_both_groups():
    pc = _proposal(id=1, text="propuesta ciudadana", author_type="citizen")
    pa = _proposal(id=2, text="propuesta academia", author_type="academia")
    s = _section(id=1, section_number="1")
    mc = _highlight_match(proposal_id=1)
    ma = _highlight_match(proposal_id=2)
    result = format_matches_for_highlights(
        [mc, ma], [s], [pc, pa], {1: "propuesta ciudadana", 2: "Univ X"}
    )
    assert "## Propuestas ciudadanas" in result
    assert "## Propuestas académicas" in result


def test_format_matches_for_highlights_empty_returns_empty_string():
    result = format_matches_for_highlights([], [], [], {})
    assert result == ""


def test_format_matches_for_highlights_skips_institution_government_ngo():
    proposals = [
        _proposal(id=1, text="inst text", author_type="institution"),
        _proposal(id=2, text="gov text", author_type="government"),
        _proposal(id=3, text="ngo text", author_type="ngo"),
    ]
    s = _section(id=1, section_number="1")
    matches = [_highlight_match(proposal_id=i) for i in (1, 2, 3)]
    result = format_matches_for_highlights(matches, [s], proposals, {})
    assert result == ""


def test_format_matches_for_highlights_includes_grado_and_senales_singular():
    p = _proposal(id=1, text="propuesta única", author_type="citizen")
    s = _section(id=1, section_number="1")
    m = _highlight_match(proposal_id=1, section_id=1, degree="alto")
    result = format_matches_for_highlights([m], [s], [p], {1: "propuesta ciudadana"})
    assert "grado alto" in result
    assert "propuesta presente en 1 sección" in result
    assert "secciones" not in result


def test_format_matches_for_highlights_includes_grado_and_senales_plural():
    p = _proposal(id=1, text="propuesta amplia", author_type="citizen")
    s1 = _section(id=1, section_number="1")
    s2 = _section(id=2, section_number="2")
    m1 = _highlight_match(proposal_id=1, section_id=1, degree="medio")
    m2 = _highlight_match(proposal_id=1, section_id=2, degree="medio")
    result = format_matches_for_highlights([m1, m2], [s1, s2], [p], {1: "propuesta ciudadana"})
    assert "propuesta presente en 2 secciones" in result


def test_format_matches_for_highlights_uses_derived_section_title():
    p = _proposal(id=1, text="propuesta", author_type="citizen")
    s = _section(id=1, text_markdown="## Artículo 5 — Tarifas reducidas\n\nbody text")
    m = _highlight_match(proposal_id=1, section_id=1)
    result = format_matches_for_highlights([m], [s], [p], {1: "propuesta ciudadana"})
    assert "Artículo 5 — Tarifas reducidas" in result
    assert "Sección" not in result


def test_format_matches_for_highlights_falls_back_to_section_number():
    p = _proposal(id=1, text="propuesta", author_type="citizen")
    s = _section(id=42, text="", text_markdown=None, section_number="3")
    m = _highlight_match(proposal_id=1, section_id=42)
    result = format_matches_for_highlights([m], [s], [p], {1: "propuesta ciudadana"})
    assert "Sección 3" in result


def test_format_matches_for_highlights_falls_back_to_id():
    p = _proposal(id=1, text="propuesta", author_type="citizen")
    s = _section(id=99, text="", text_markdown=None, section_number=None)
    m = _highlight_match(proposal_id=1, section_id=99)
    result = format_matches_for_highlights([m], [s], [p], {1: "propuesta ciudadana"})
    assert "[id 99]" in result


# ---------------------------------------------------------------------------
# format_curated_stats
# ---------------------------------------------------------------------------


def test_format_curated_stats_empty_returns_sin_datos():
    assert format_curated_stats({}) == "(sin datos)"


def test_format_curated_stats_pct_formatted_as_percent():
    result = format_curated_stats({"pct_sections_matched": 0.42})
    assert "42%" in result


def test_format_curated_stats_alto_medio_only_when_both_present():
    result_both = format_curated_stats({"alto_count": 3, "medio_count": 2})
    assert "alto" in result_both.lower()
    assert "medio" in result_both.lower()

    result_only_alto = format_curated_stats({"alto_count": 3})
    assert "alto" not in result_only_alto.lower()
