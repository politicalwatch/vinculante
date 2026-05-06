from vinculante.application.summary.formatter import format_summary
from vinculante.application.summary.schemas import (
    DocumentOverview,
    GapAnalysis,
    Highlight,
    HighlightExtraction,
    Synthesis,
    ThematicCluster,
    ThemeAnalysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _overview(intro: str = "intro text", axes: list[str] | None = None) -> DocumentOverview:
    return DocumentOverview(intro=intro, axes=axes or ["eje 1", "eje 2"])


def _themes(labels: list[str] | None = None) -> ThemeAnalysis:
    labels = labels or ["Tema A"]
    return ThemeAnalysis(clusters=[ThematicCluster(label=l, description=f"desc {l}") for l in labels])


def _highlights(n: int = 1) -> HighlightExtraction:
    return HighlightExtraction(highlights=[
        Highlight(author_label="aut", proposal_claim="claim", section_ref="Sección 1 (p. 1)", relevance="relevant")
        for _ in range(n)
    ])


def _gaps(orphan: str = "", unmatched: str = "", narrative: str = "") -> GapAnalysis:
    return GapAnalysis(orphan_observations=orphan, unmatched_clusters=unmatched, gaps_narrative=narrative)


def _synthesis(vision: str = "vision texto", observaciones: list[str] | None = None) -> Synthesis:
    return Synthesis(vision_general=vision, observaciones=observaciones or [])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_format_summary_all_none_returns_empty():
    assert format_summary(None, None, None, None, None) == ""


def test_format_summary_only_overview_contains_principals_ejes():
    result = format_summary(_overview(), None, None, None, None)
    assert "## Principales ejes" in result
    assert "intro text" in result
    assert "- eje 1" in result


def test_format_summary_only_overview_no_other_sections():
    result = format_summary(_overview(), None, None, None, None)
    assert "## Visión general" not in result
    assert "## Áreas de mayor vinculación" not in result
    assert "## Vinculaciones destacadas" not in result
    assert "## Lagunas detectadas" not in result
    assert "## Observaciones" not in result


def test_format_summary_only_synthesis_vision_general():
    result = format_summary(None, None, None, None, _synthesis(vision="la visión"))
    assert "## Visión general" in result
    assert "la visión" in result


def test_format_summary_synthesis_no_observaciones_section_when_empty():
    result = format_summary(None, None, None, None, _synthesis(observaciones=[]))
    assert "## Observaciones" not in result


def test_format_summary_synthesis_with_observaciones():
    result = format_summary(None, None, None, None, _synthesis(observaciones=["obs 1", "obs 2"]))
    assert "## Observaciones" in result
    assert "- obs 1" in result
    assert "- obs 2" in result


def test_format_summary_only_themes():
    result = format_summary(None, _themes(["Vivienda"]), None, None, None)
    assert "## Áreas de mayor vinculación" in result
    assert "**Vivienda**" in result


def test_format_summary_only_highlights():
    result = format_summary(None, None, _highlights(), None, None)
    assert "## Vinculaciones destacadas" in result
    assert "**aut**" in result


def test_format_summary_gaps_all_empty_fields_no_section():
    result = format_summary(None, None, None, _gaps("", "", ""), None)
    assert "## Lagunas detectadas" not in result


def test_format_summary_gaps_only_narrative():
    result = format_summary(None, None, None, _gaps(narrative="hay lagunas"), None)
    assert "## Lagunas detectadas" in result
    assert "hay lagunas" in result


def test_format_summary_gaps_only_orphan():
    result = format_summary(None, None, None, _gaps(orphan="secciones sin vinculación"), None)
    assert "## Lagunas detectadas" in result


def test_format_summary_section_order():
    result = format_summary(_overview(), _themes(), _highlights(), _gaps(narrative="g"), _synthesis())
    ejes_pos = result.index("## Principales ejes")
    vision_pos = result.index("## Visión general")
    areas_pos = result.index("## Áreas de mayor vinculación")
    vinculaciones_pos = result.index("## Vinculaciones destacadas")
    lagunas_pos = result.index("## Lagunas detectadas")
    assert ejes_pos < vision_pos < areas_pos < vinculaciones_pos < lagunas_pos


def test_format_summary_no_trailing_blank_line():
    result = format_summary(_overview(), _themes(), None, None, None)
    assert not result.endswith("\n")
    assert not result.endswith("\n\n")
