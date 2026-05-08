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
    return ThemeAnalysis(
        clusters=[ThematicCluster(label=lbl, description=f"desc {lbl}") for lbl in labels]
    )


def _highlight(author: str = "aut") -> Highlight:
    return Highlight(
        author_label=author,
        proposal_claim="claim",
        section_ref="Sección 1 (p. 1)",
        relevance="relevant",
    )


def _highlights(
    citizen: int = 0,
    academia: int = 0,
    citizen_intro: str = "Las propuestas ciudadanas destacan:",
    academia_intro: str = "Las propuestas académicas reflejan:",
) -> HighlightExtraction:
    return HighlightExtraction(
        citizen_intro=citizen_intro if citizen else "",
        citizen_highlights=[_highlight("propuesta ciudadana") for _ in range(citizen)],
        academia_intro=academia_intro if academia else "",
        academia_highlights=[_highlight("Univ X") for _ in range(academia)],
    )


def _gaps(
    orphan: str = "",
    citizen: str = "",
    academia: str = "",
    narrative: str = "",
) -> GapAnalysis:
    return GapAnalysis(
        orphan_observations=orphan,
        citizen_unmatched=citizen,
        academia_unmatched=academia,
        gaps_narrative=narrative,
    )


def _synthesis(vision: str = "vision texto") -> Synthesis:
    return Synthesis(vision_general=vision)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_format_summary_all_none_returns_empty():
    assert format_summary(None, None, None, None, None) == ""


def test_format_summary_only_overview_contains_resumen_ley():
    result = format_summary(_overview(), None, None, None, None)
    assert "## Resumen de la ley" in result
    assert "intro text" in result
    assert "- eje 1" in result


def test_format_summary_only_overview_no_other_sections():
    result = format_summary(_overview(), None, None, None, None)
    assert "## Resumen de las vinculaciones detectadas" not in result
    assert "## Áreas de mayor vinculación" not in result
    assert "## Vinculaciones destacadas" not in result
    assert "## Propuestas no recogidas" not in result
    assert "## Observaciones" not in result


def test_format_summary_only_synthesis_vision_general():
    result = format_summary(None, None, None, None, _synthesis(vision="la visión"))
    assert "## Resumen de las vinculaciones detectadas" in result
    assert "la visión" in result


def test_format_summary_no_observaciones_section():
    result = format_summary(None, None, None, None, _synthesis())
    assert "## Observaciones" not in result


def test_format_summary_only_themes():
    result = format_summary(None, _themes(["Vivienda"]), None, None, None)
    assert "## Resumen de las vinculaciones detectadas" in result
    assert "## Áreas de mayor vinculación" not in result
    assert "**Vivienda**" in result
    assert "Las áreas con mayor vinculación son:" not in result


def test_format_summary_synthesis_and_themes_show_lead_in():
    result = format_summary(None, _themes(["Vivienda"]), None, None, _synthesis(vision="la visión"))
    assert "Las áreas con mayor vinculación son:" in result
    assert "**Vivienda**" in result


def test_format_summary_highlights_citizen_only():
    result = format_summary(None, None, _highlights(citizen=1), None, None)
    assert "## Vinculaciones destacadas" in result
    assert "Las propuestas ciudadanas destacan:" in result
    assert "**propuesta ciudadana**" in result
    assert "Las propuestas académicas reflejan:" not in result


def test_format_summary_highlights_academia_only():
    result = format_summary(None, None, _highlights(academia=1), None, None)
    assert "## Vinculaciones destacadas" in result
    assert "Las propuestas académicas reflejan:" in result
    assert "**Univ X**" in result
    assert "Las propuestas ciudadanas destacan:" not in result


def test_format_summary_highlights_both_groups():
    result = format_summary(None, None, _highlights(citizen=1, academia=1), None, None)
    assert "## Vinculaciones destacadas" in result
    assert "Las propuestas ciudadanas destacan:" in result
    assert "Las propuestas académicas reflejan:" in result
    assert "**propuesta ciudadana**" in result
    assert "**Univ X**" in result


def test_format_summary_highlights_empty_no_section():
    result = format_summary(None, None, _highlights(), None, None)
    assert "## Vinculaciones destacadas" not in result


def test_format_summary_gaps_all_empty_fields_no_section():
    result = format_summary(None, None, None, _gaps(), None)
    assert "## Propuestas no recogidas" not in result


def test_format_summary_gaps_only_narrative():
    result = format_summary(None, None, None, _gaps(narrative="hay lagunas"), None)
    assert "## Propuestas no recogidas" in result
    assert "hay lagunas" in result


def test_format_summary_gaps_only_citizen():
    result = format_summary(None, None, None, _gaps(citizen="ciudadanos sin vinculación"), None)
    assert "## Propuestas no recogidas" in result
    assert "ciudadanos sin vinculación" in result


def test_format_summary_gaps_only_academia():
    result = format_summary(None, None, None, _gaps(academia="academia sin vinculación"), None)
    assert "## Propuestas no recogidas" in result
    assert "academia sin vinculación" in result


def test_format_summary_gaps_full_four_fields_in_order():
    result = format_summary(
        None, None, None,
        _gaps(orphan="huérfanas", citizen="ciudadanos", academia="académicos", narrative="síntesis"),
        None,
    )
    orphan_pos = result.index("huérfanas")
    citizen_pos = result.index("ciudadanos")
    academia_pos = result.index("académicos")
    narrative_pos = result.index("síntesis")
    assert orphan_pos < citizen_pos < academia_pos < narrative_pos


def test_format_summary_section_order():
    result = format_summary(
        _overview(),
        _themes(),
        _highlights(citizen=1),
        _gaps(narrative="g"),
        _synthesis(),
    )
    resumen_ley_pos = result.index("## Resumen de la ley")
    resumen_vinc_pos = result.index("## Resumen de las vinculaciones detectadas")
    lead_in_pos = result.index("Las áreas con mayor vinculación son:")
    vinculaciones_pos = result.index("## Vinculaciones destacadas")
    propuestas_pos = result.index("## Propuestas no recogidas")
    assert resumen_ley_pos < resumen_vinc_pos < lead_in_pos < vinculaciones_pos < propuestas_pos
    assert "## Áreas de mayor vinculación" not in result
    assert "## Observaciones" not in result


def test_format_summary_no_trailing_blank_line():
    result = format_summary(_overview(), _themes(), None, None, None)
    assert not result.endswith("\n")
    assert not result.endswith("\n\n")
