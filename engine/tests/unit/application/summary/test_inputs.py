from types import SimpleNamespace

from vinculante.application.summary.inputs import (
    anonymise_author,
    curate_stats,
    find_orphan_sections,
    find_unmatched_proposals_with_ninguno,
    format_curated_stats,
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
    is_matchable: bool = True,
    section_number: str | None = None,
    page_number: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(id=id, text=text, is_matchable=is_matchable, section_number=section_number, page_number=page_number)


def _proposal(*, id: int = 1, text: str = "x" * 90, author: str | None = None, author_type: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=id, text=text, author=author, author_type=author_type)


def _match(*, proposal_id: int = 1, section_id: int = 1, degree: str = "alto", confidence: float = 0.9, explanation: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(proposal_id=proposal_id, section_id=section_id, degree=degree, confidence=confidence, explanation=explanation)


# ---------------------------------------------------------------------------
# anonymise_author
# ---------------------------------------------------------------------------


def test_anonymise_author_tracer():
    assert anonymise_author(None, "ciudadana") == "propuesta ciudadana"


def test_anonymise_author_citizen_types():
    for t in ("citizen", "ciudadano", "ciudadana", "individual", "independiente"):
        assert anonymise_author("Real Name", t) == "propuesta ciudadana"


def test_anonymise_author_none_author_type():
    assert anonymise_author("any", None) == "propuesta ciudadana"


def test_anonymise_author_empty_author_type():
    assert anonymise_author("any", "") == "propuesta ciudadana"


def test_anonymise_author_non_citizen_with_author():
    assert anonymise_author("Ministerio de Hacienda", "ministerio") == "Ministerio de Hacienda"


def test_anonymise_author_non_citizen_without_author():
    assert anonymise_author(None, "asociacion") == "propuesta ciudadana"


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
    p = _proposal(id=1, text="x" * 90)
    m_alto = _match(proposal_id=1, degree="alto")
    result = find_unmatched_proposals_with_ninguno([p], [m_alto])
    assert result == []


def test_find_unmatched_excludes_text_below_80():
    p = _proposal(id=1, text="x" * 79)
    assert find_unmatched_proposals_with_ninguno([p], []) == []


def test_find_unmatched_includes_eligible_no_ninguno():
    p = _proposal(id=1, text="x" * 80)
    result = find_unmatched_proposals_with_ninguno([p], [])
    assert len(result) == 1
    assert result[0]["proposal"] is p
    assert result[0]["representative_ninguno"] is None


def test_find_unmatched_picks_highest_confidence_ninguno():
    p = _proposal(id=1, text="x" * 80)
    m_low = _match(proposal_id=1, degree="ninguno", confidence=0.3, explanation="x" * 35)
    m_high = _match(proposal_id=1, degree="ninguno", confidence=0.8, explanation="y" * 35)
    result = find_unmatched_proposals_with_ninguno([p], [m_low, m_high])
    assert result[0]["representative_ninguno"] == "y" * 35


def test_find_unmatched_skips_ninguno_explanation_below_30():
    p = _proposal(id=1, text="x" * 80)
    m = _match(proposal_id=1, degree="ninguno", confidence=0.9, explanation="short")
    result = find_unmatched_proposals_with_ninguno([p], [m])
    assert result[0]["representative_ninguno"] is None


def test_find_unmatched_truncates_ninguno_explanation_to_300():
    p = _proposal(id=1, text="x" * 80)
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


def test_format_unmatched_proposals_includes_ninguno_explanation():
    p = _proposal(id=1, text="mi propuesta")
    item = {"proposal": p, "representative_ninguno": "razón detallada"}
    result = format_unmatched_proposals([item])
    assert "mi propuesta" in result
    assert "razón detallada" in result


def test_format_unmatched_proposals_no_explanation():
    p = _proposal(id=1, text="mi propuesta")
    item = {"proposal": p, "representative_ninguno": None}
    result = format_unmatched_proposals([item])
    assert "mi propuesta" in result
    assert "Razón" not in result


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
