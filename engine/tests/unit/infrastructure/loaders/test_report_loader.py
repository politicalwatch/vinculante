"""Unit tests for ReportLoader.

The loader unit tests use fully mocked Docling objects (no filesystem access,
no LLM calls). Tests gated by REPORT_INTEGRATION_TESTS env var run against
the real sample files and require a working LLM config.
"""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vinculante.application.ingestion.report_schemas import (
    AuthorExtraction,
    ExtractedProposal,
    ExtractedProposalList,
)
from vinculante.infrastructure.loaders.report_loader import (
    ReportLoader,
    _clean_heading,
    _compute_topic_subtopic,
    _dedup_by_reference,
    _dedup_seed_tokens,
    _is_subitem_heading,
    _is_verbatim,
    _make_ref,
    _normalize,
    _slugify,
    _strip_field_prefixes,
)

REAL_SAMPLES = Path(__file__).parents[4] / "data" / "real" / "proposals" / "academia"
NEEDS_LLM = pytest.mark.skipif(
    not os.environ.get("REPORT_INTEGRATION_TESTS"),
    reason="Set REPORT_INTEGRATION_TESTS=1 to run real-file tests (requires LLM config)",
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_table_item(grid: list[list[str]]) -> MagicMock:
    cells = []
    for r, row in enumerate(grid):
        for c, text in enumerate(row):
            cell = MagicMock()
            cell.text = text
            cell.start_row_offset_idx = r
            cell.start_col_offset_idx = c
            cells.append(cell)
    table_data = MagicMock()
    table_data.num_rows = len(grid)
    table_data.num_cols = len(grid[0]) if grid else 0
    table_data.table_cells = cells
    item = MagicMock()
    item.label = "table"
    item.text = None
    item.data = table_data
    return item


def _make_heading_item(text: str, level: int = 1) -> MagicMock:
    item = MagicMock()
    item.label = "section_header"
    item.text = text
    item.level = level
    return item


def _make_text_item(text: str) -> MagicMock:
    item = MagicMock()
    item.label = "text"
    item.text = text
    return item


def _make_llm(
    author: str = "Test Author",
    proposals: list[ExtractedProposal] | None = None,
) -> MagicMock:
    author_chain = MagicMock()
    author_chain.invoke.return_value = AuthorExtraction(author=author)
    extract_chain = MagicMock()
    extract_chain.invoke.return_value = ExtractedProposalList(proposals=proposals or [])

    llm = MagicMock()
    llm.with_structured_output.side_effect = lambda schema: (
        author_chain if schema is AuthorExtraction else extract_chain
    )
    return llm


def _make_loader_with_items(
    doc_items: list[tuple[MagicMock, int]],
    author: str = "Test Author",
    llm: MagicMock | None = None,
) -> ReportLoader:
    """Build a ReportLoader backed by a mocked doc with the given items."""
    llm = llm or _make_llm(author=author)
    with patch("vinculante.infrastructure.loaders.report_loader.DocumentConverter"):
        loader = ReportLoader(llm=llm)

    # Prepend an author text item so _extract_author picks it up
    author_item = _make_text_item(f"Autor: {author}")
    all_items: list[tuple[MagicMock, int]] = [(author_item, 0)] + list(doc_items)

    doc = MagicMock()
    doc.iterate_items.return_value = all_items  # list — re-iterable across both calls
    loader._converter = MagicMock()
    loader._converter.convert.return_value = MagicMock(document=doc)
    return loader


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_normalize_strips_accents_and_lowercases():
    assert _normalize("TÍTULO") == "titulo"
    assert _normalize("Explicación  Y  Posición") == "explicacion y posicion"


def test_slugify_truncates_at_80():
    assert len(_slugify("a" * 200)) <= 80


def test_is_verbatim_matches_substring():
    assert _is_verbatim("la medida consiste en", "En detalle, la medida consiste en algo.")


def test_is_verbatim_normalizes_whitespace():
    assert _is_verbatim("texto  con\nespacios", "previo texto  con\nespacios final")


def test_is_verbatim_fails_on_mismatch():
    assert not _is_verbatim("texto inventado", "texto original")


def test_make_ref_deduplicates():
    seen: dict[str, int] = {}
    r1 = _make_ref("propuesta uno", seen)
    r2 = _make_ref("propuesta uno", seen)
    assert r1 != r2
    assert r2 == f"{r1}-1"


def test_compute_topic_subtopic_empty():
    assert _compute_topic_subtopic([]) == (None, None)


def test_compute_topic_subtopic_one_heading():
    assert _compute_topic_subtopic(["Eje 1"]) == ("Eje 1", None)


def test_compute_topic_subtopic_two_headings():
    assert _compute_topic_subtopic(["Eje 1", "Sección 1.1"]) == ("Eje 1", "Sección 1.1")


def test_compute_topic_subtopic_three_headings_uses_deepest_two():
    result = _compute_topic_subtopic(["H1", "H2", "H3"])
    assert result == ("H2", "H3")


def test_compute_topic_subtopic_skips_empty_strings():
    result = _compute_topic_subtopic(["Eje 1", "", "Subsección"])
    assert result == ("Eje 1", "Subsección")


def test_clean_heading_strips_hashes():
    assert _clean_heading("## Medidas económicas") == "Medidas económicas"
    assert _clean_heading("# Sección 1") == "Sección 1"
    assert _clean_heading("Sección sin prefijo") == "Sección sin prefijo"


def test_clean_heading_none_and_empty():
    assert _clean_heading(None) is None
    assert _clean_heading("") is None
    assert _clean_heading("###") is None


def test_is_subitem_heading_propuesta_and_medida():
    assert _is_subitem_heading("Propuesta 1: Estado emprendedor")
    assert _is_subitem_heading("Medida 7")
    assert _is_subitem_heading("Criterio 3")
    assert _is_subitem_heading("Argumento 2")


def test_is_subitem_heading_nested_numbers():
    assert _is_subitem_heading("2.1. Definición de juventud")
    assert _is_subitem_heading("3.1.1.Vivienda")


def test_is_subitem_heading_theme_is_not_subitem():
    assert not _is_subitem_heading("Derechos Económicos y Cobertura Social")
    assert not _is_subitem_heading("III. ARGUMENTOS PLANTEADO POR DISCIPLINAS")
    assert not _is_subitem_heading("Salud Mental y Bienestar")
    assert not _is_subitem_heading("1. Ciencias Políticas")


def test_dedup_seed_tokens_removes_duplicates():
    assert _dedup_seed_tokens("Propuesta 1 Estado emprendedor Propuesta 1") == "Propuesta 1 Estado emprendedor"
    assert _dedup_seed_tokens("medida medida medida texto") == "medida texto"


def test_dedup_seed_tokens_preserves_unique():
    assert _dedup_seed_tokens("Estado emprendedor innovacion") == "Estado emprendedor innovacion"


# ---------------------------------------------------------------------------
# Heading state machine — PDF (flat level=1) and DOCX (explicit levels)
# ---------------------------------------------------------------------------


def test_pdf_bodyless_theme_heading_captured():
    """body-less theme heading (no text beneath) updates current_theme."""
    grid = [
        ["Título", "Desarrollo"],
        ["Propuesta X", "El Estado debe garantizar el acceso."],
    ]
    table_item = _make_table_item(grid)
    # PDF: all level=1; theme heading has no body text between it and the subitem
    theme = _make_heading_item("Trabajo digno", level=1)
    subitem = _make_heading_item("Propuesta 1: Estado emprendedor", level=1)

    loader = _make_loader_with_items([(theme, 0), (subitem, 0), (table_item, 0)])
    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert rows[0]["topic"] == "Trabajo digno"
    assert rows[0]["subtopic"] == "Propuesta 1: Estado emprendedor"


def test_pdf_theme_and_subitem_heading_regex_classification():
    """PDF flat headings: non-propuesta heading → theme; propuesta/X.Y heading → subitem."""
    body = _make_text_item("El Estado debe garantizar el acceso a la vivienda. " * 3)
    proposals = [
        ExtractedProposal(
            text="El Estado debe garantizar el acceso a la vivienda.",
            topic="2. PROPUESTAS",
            subtopic="2.1. Definición",
        )
    ]
    llm = _make_llm(proposals=proposals)
    theme = _make_heading_item("2. PROPUESTAS", level=1)
    subitem = _make_heading_item("2.1. Definición de juventud", level=1)

    loader = _make_loader_with_items([(theme, 0), (subitem, 0), (body, 0)], llm=llm)
    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert rows[0]["topic"] == "2. PROPUESTAS"
    assert rows[0]["subtopic"] == "2.1. Definición"


def test_docx_level_based_classification():
    """DOCX explicit heading levels: level 2 → theme, level 3 → subitem."""
    grid = [
        ["Título", "Desarrollo"],
        ["Argumento A", "Los jóvenes de 16 deben poder votar."],
    ]
    table_item = _make_table_item(grid)
    theme = _make_heading_item("III. ARGUMENTOS", level=2)
    subitem = _make_heading_item("1. Ciencias Políticas", level=3)

    loader = _make_loader_with_items([(theme, 0), (subitem, 0), (table_item, 0)])
    rows = loader.load("fake.docx")

    assert len(rows) == 1
    assert rows[0]["topic"] == "III. ARGUMENTOS"
    assert rows[0]["subtopic"] == "1. Ciencias Políticas"


# ---------------------------------------------------------------------------
# Tier 1 — structural table extraction
# ---------------------------------------------------------------------------


def test_tier1_extracts_titulo_desarrollo_table():
    grid = [
        ["Título", "Desarrollo"],
        ["Voto a los 16", "Los jóvenes de 16 años deben poder votar."],
        ["Educación política", "Formación ciudadana en centros educativos."],
    ]
    table_item = _make_table_item(grid)
    theme = _make_heading_item("Argumentos", level=2)
    subitem = _make_heading_item("Ciencias Políticas", level=3)

    loader = _make_loader_with_items([(theme, 0), (subitem, 0), (table_item, 0)])
    rows = loader.load("fake.pdf")

    assert len(rows) == 2
    assert rows[0]["topic"] == "Argumentos"
    assert rows[0]["subtopic"] == "Ciencias Políticas"
    assert "Voto a los 16" in rows[0]["text"]
    assert "Los jóvenes de 16 años" in rows[0]["text"]
    assert rows[0]["author"] == "Test Author"


def test_tier1_accepts_criterio_explicacion_headers():
    grid = [
        ["Criterio", "Explicación y posición"],
        ["Madurez suficiente", "Los adolescentes de 16 años tienen capacidad de decisión."],
    ]
    table_item = _make_table_item(grid)
    loader = _make_loader_with_items(
        [(_make_heading_item("Argumentos"), (0)), (table_item, 0)]
    )

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert "Madurez suficiente" in rows[0]["text"]


def test_tier1_skips_four_column_table_falls_to_export_markdown():
    """4-col tables (PROPUESTA|ODS|INDICADORES|META) fall through to export_to_markdown."""
    grid = [
        ["Propuesta", "ODS", "Indicadores", "Meta"],
        ["Estado emprendedor: El Estado debe...", "8", "% PIB en I+D", "2030: 3%"],
    ]
    table_item = _make_table_item(grid)
    md = "| Propuesta | ODS | Indicadores | Meta |\n|---|---|---|---|\n| Estado emprendedor | 8 | % PIB | 3% |"
    table_item.export_to_markdown.return_value = md

    proposals = [
        ExtractedProposal(text="Estado emprendedor: El Estado debe liderar la inversion en I+D.")
    ]
    llm = _make_llm(proposals=proposals)
    loader = _make_loader_with_items([(table_item, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    table_item.export_to_markdown.assert_called_once()
    assert len(rows) == 1
    assert "Estado emprendedor" in rows[0]["text"]


def test_tier1_skips_table_without_matching_headers():
    grid = [
        ["Nombre", "Apellidos", "Universidad"],
        ["Ana", "García López", "UCM"],
    ]
    table_item = _make_table_item(grid)
    table_item.export_to_markdown.return_value = ""
    loader = _make_loader_with_items([(_make_heading_item("Autores"), 0), (table_item, 0)])

    rows = loader.load("fake.pdf")

    assert len(rows) == 0


def test_tier1_skips_empty_data_rows():
    grid = [
        ["Título", "Desarrollo"],
        ["", ""],
        ["Voto a los 16", "Los jóvenes deben poder votar."],
    ]
    table_item = _make_table_item(grid)
    loader = _make_loader_with_items([(_make_heading_item("Argumentos"), 0), (table_item, 0)])

    rows = loader.load("fake.pdf")

    assert len(rows) == 1


def test_tier1_skips_body_empty_rows():
    """Rows with title only (no body) are category sub-headers, not proposals."""
    grid = [
        ["Título", "Desarrollo"],
        ["ARGUMENTOS NORMATIVOS", ""],        # header-only row — should be skipped
        ["Madurez política", "Los adolescentes de 16 años tienen capacidad de decisión."],
    ]
    table_item = _make_table_item(grid)
    loader = _make_loader_with_items([(_make_heading_item("Argumentos"), 0), (table_item, 0)])

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert "Madurez política" in rows[0]["text"]


# ---------------------------------------------------------------------------
# Tier 1 ↔ Tier 2 coverage gating
# ---------------------------------------------------------------------------


def test_post_tier1_prose_under_same_subitem_is_skipped():
    """Post-table prose under a Tier1-covered (theme, subitem) is not sent to LLM."""
    grid = [
        ["Título", "Desarrollo"],
        ["Argumento A", "Los jóvenes de 16 deben poder votar."],
    ]
    table_item = _make_table_item(grid)
    post_prose = _make_text_item("Este argumento resume lo expuesto en la tabla anterior.")
    theme = _make_heading_item("III. Argumentos", level=2)
    subitem = _make_heading_item("1. Ciencias Políticas", level=3)

    author_chain = MagicMock()
    author_chain.invoke.return_value = AuthorExtraction(author="Test Author")
    extract_chain = MagicMock()
    extract_chain.invoke.return_value = ExtractedProposalList(proposals=[])
    llm = MagicMock()
    llm.with_structured_output.side_effect = lambda schema: (
        author_chain if schema is AuthorExtraction else extract_chain
    )

    loader = _make_loader_with_items(
        [(theme, 0), (subitem, 0), (table_item, 0), (post_prose, 0)], llm=llm
    )
    rows = loader.load("fake.docx")

    assert len(rows) == 1
    assert "Argumento A" in rows[0]["text"]
    # Post-table prose must not appear in the LLM blob (author preamble may still be sent)
    if extract_chain.invoke.called:
        call_text = extract_chain.invoke.call_args[0][0]
        assert "Este argumento resume" not in call_text


def test_pre_tier1_prose_under_same_subitem_is_preserved():
    """Pre-table intro prose arrives before the Tier1 key is set, so it reaches the LLM."""
    grid = [
        ["Título", "Desarrollo"],
        ["Argumento A", "Los jóvenes de 16 deben poder votar."],
    ]
    table_item = _make_table_item(grid)
    pre_prose = _make_text_item("Introducción a las perspectivas disciplinares.")
    theme = _make_heading_item("III. Argumentos", level=2)
    subitem = _make_heading_item("1. Ciencias Políticas", level=3)

    proposals = [ExtractedProposal(text="Introducción a las perspectivas disciplinares.")]
    llm = _make_llm(proposals=proposals)

    loader = _make_loader_with_items(
        [(theme, 0), (subitem, 0), (pre_prose, 0), (table_item, 0)], llm=llm
    )
    rows = loader.load("fake.docx")

    # 1 Tier 1 row + 1 LLM row from pre-table prose
    assert len(rows) == 2
    assert any("Argumento A" in r["text"] for r in rows)
    assert any("Introducción" in r["text"] for r in rows)


def test_sibling_subitem_prose_preserved():
    """Prose under a sibling (theme, subitem) pair is not filtered by Tier1 coverage."""
    grid = [
        ["Título", "Desarrollo"],
        ["Argumento S1", "Argumento desde Ciencias Políticas."],
    ]
    table_item = _make_table_item(grid)
    s2_prose = _make_text_item("Los sociólogos señalan que la participación juvenil mejora la democracia.")
    theme = _make_heading_item("III. Argumentos", level=2)
    s1 = _make_heading_item("1. Ciencias Políticas", level=3)
    s2 = _make_heading_item("2. Sociología", level=3)

    proposals = [
        ExtractedProposal(
            text="Los sociólogos señalan que la participación juvenil mejora la democracia.",
            topic="III. Argumentos",
            subtopic="2. Sociología",
        )
    ]
    llm = _make_llm(proposals=proposals)

    loader = _make_loader_with_items(
        [(theme, 0), (s1, 0), (table_item, 0), (s2, 0), (s2_prose, 0)], llm=llm
    )
    rows = loader.load("fake.docx")

    assert len(rows) == 2
    tier1_row = next(r for r in rows if "Argumento S1" in r["text"])
    llm_row = next(r for r in rows if "sociólogos" in r["text"])
    assert tier1_row["subtopic"] == "1. Ciencias Políticas"
    assert llm_row["subtopic"] == "2. Sociología"


def test_llm_path_skips_duplicate_title():
    """LLM path: no double-prepend when p.text already begins with p.title."""
    proposals = [
        ExtractedProposal(
            title="Etiquetado digital",
            text="Etiquetado digital. Se prohibirá el acceso de menores a videojuegos con cajas.",
            topic="Videojuegos",
        )
    ]
    llm = _make_llm(proposals=proposals)

    prose = "Etiquetado digital. Se prohibirá el acceso de menores a videojuegos con cajas. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items([(_make_heading_item("Videojuegos"), 0), (body, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert rows[0]["text"].startswith("Etiquetado digital.")
    assert not rows[0]["text"].startswith("Etiquetado digital\n\nEtiquetado digital")


def test_llm_path_skips_medida_label_title():
    """LLM path: 'Medida N' / 'Medida número N' labels are NOT prepended to text."""
    proposals = [
        ExtractedProposal(
            title="Medida 7",
            text="Los fabricantes deberán configurar protecciones por defecto para menores.",
            topic="Medidas de regulación",
        )
    ]
    llm = _make_llm(proposals=proposals)

    prose = "Los fabricantes deberán configurar protecciones por defecto para menores. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items(
        [(_make_heading_item("Medidas de regulación"), 0), (body, 0)], llm=llm
    )

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert not rows[0]["text"].startswith("Medida 7")
    assert "fabricantes" in rows[0]["text"]


def test_section_header_medida_label_kept_inline():
    """section_header 'Medida número N' is treated as inline text, not a heading update."""
    medida_label = _make_heading_item("Medida número 2", level=1)
    body = _make_text_item("Los dispositivos deben incluir sistemas de control parental.")

    proposals = [
        ExtractedProposal(
            text="Los dispositivos deben incluir sistemas de control parental.",
            topic="Medidas de regulación de la industria",
        )
    ]
    llm = _make_llm(proposals=proposals)

    theme = _make_heading_item("Medidas de regulación de la industria", level=1)
    loader = _make_loader_with_items(
        [(theme, 0), (medida_label, 0), (body, 0)], llm=llm
    )

    # Capture what the LLM receives
    extract_chain = llm.with_structured_output.side_effect(ExtractedProposalList)
    rows = loader.load("fake.pdf")

    # The label must appear inline in the LLM blob (not as a ## heading)
    assert extract_chain.invoke.called
    call_text = extract_chain.invoke.call_args[0][0]
    assert "Medida número 2" in call_text
    assert "## Medida número 2" not in call_text
    # topic should come from the LLM response (semantic heading, not the label)
    assert rows[0]["topic"] == "Medidas de regulación de la industria"


# ---------------------------------------------------------------------------
# Field-prefix stripping (_strip_field_prefixes + integration in LLM path)
# ---------------------------------------------------------------------------


def test_strip_field_prefixes_titulo():
    assert _strip_field_prefixes("Título. Sistemas de verificación de edad.") == \
        "Sistemas de verificación de edad."


def test_strip_field_prefixes_descripcion():
    assert _strip_field_prefixes("Descripción: imposición a todos los actores.") == \
        "imposición a todos los actores."


def test_strip_field_prefixes_midline_not_stripped():
    """Mid-line occurrences are NOT stripped (only line-start via MULTILINE)."""
    text = "El texto dice Título. X y más cosas."
    assert _strip_field_prefixes(text) == text


def test_llm_path_strips_titulo_prefix():
    """LLM output: 'Título. X…' → resulting text starts with 'X', no prefix."""
    proposals = [
        ExtractedProposal(
            text="Título. Sistemas de verificación de edad.\n\nLos fabricantes deberán integrar SVE.",
            topic="Medidas de regulación",
        )
    ]
    llm = _make_llm(proposals=proposals)
    prose = "Título. Sistemas de verificación de edad. Los fabricantes deberán integrar SVE. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items(
        [(_make_heading_item("Medidas de regulación"), 0), (body, 0)], llm=llm
    )
    rows = loader.load("fake.pdf")
    assert len(rows) == 1
    assert not rows[0]["text"].startswith("Título.")
    assert rows[0]["text"].startswith("Sistemas de verificación de edad.")


def test_llm_path_no_duplicate_when_titulo_prefix():
    """p.title = título sentence, p.text starts with 'Título. <same>' → no duplication."""
    proposals = [
        ExtractedProposal(
            title="Sistemas de verificación de edad",
            text="Título. Sistemas de verificación de edad.\n\nLos fabricantes deberán integrar SVE.",
            topic="Medidas de regulación",
        )
    ]
    llm = _make_llm(proposals=proposals)
    prose = "Título. Sistemas de verificación de edad. Los fabricantes deberán integrar SVE. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items(
        [(_make_heading_item("Medidas de regulación"), 0), (body, 0)], llm=llm
    )
    rows = loader.load("fake.pdf")
    assert len(rows) == 1
    text = rows[0]["text"]
    assert text.startswith("Sistemas de verificación de edad.")
    assert "Sistemas de verificación de edad.\n\nSistemas de verificación" not in text


def test_table_markdown_reaches_llm_and_output_is_stripped():
    """Table markdown with 'Título. X' cells passes to LLM; output strip cleans the result."""
    grid = [
        ["Nombre", "Apellidos", "Universidad"],
        ["Ana", "García López", "UCM"],
    ]
    table_item = _make_table_item(grid)
    table_item.export_to_markdown.return_value = (
        "| Título. Sistemas de verificación | Descripción: imposición |\n"
        "| --- | --- |"
    )
    # LLM sees the table markdown and returns text with prefix (realistic)
    proposals = [ExtractedProposal(
        text="Título. Sistemas de verificación.\nDescripción: imposición a todos.",
        topic="Temas",
    )]
    llm = _make_llm(proposals=proposals)
    loader = _make_loader_with_items([(_make_heading_item("Temas"), 0), (table_item, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    # Output-level strip removes the prefixes from the final row text
    assert len(rows) == 1
    assert not rows[0]["text"].startswith("Título.")
    assert "Descripción:" not in rows[0]["text"]
    assert "Sistemas de verificación." in rows[0]["text"]


# ---------------------------------------------------------------------------
# Tier 2 — LLM section extraction
# ---------------------------------------------------------------------------


def test_tier2_calls_llm_for_prose_section():
    proposals = [
        ExtractedProposal(
            title="Medida 1",
            text="Medida 1. La nueva Ley debe garantizar la presencia de centros juveniles.",
            topic="2. Propuestas",
            subtopic="2.1 Ley de Juventud",
        ),
        ExtractedProposal(
            title="Medida 2",
            text="Medida 2. Los planes de estudios deben incluir educacion financiera.",
            topic="2. Propuestas",
            subtopic="2.1 Ley de Juventud",
        ),
    ]
    llm = _make_llm(author="Kilian Wirthwein, Javier Carbonell", proposals=proposals)

    long_prose = "Medida 1. La nueva Ley debe garantizar la presencia de centros juveniles. " * 3
    body = _make_text_item(long_prose)
    theme = _make_heading_item("2. Propuestas", level=1)
    subitem = _make_heading_item("2.1 Ley de Juventud", level=1)

    loader = _make_loader_with_items(
        [(theme, 0), (subitem, 0), (body, 0)],
        author="Kilian Wirthwein, Javier Carbonell",
        llm=llm,
    )

    rows = loader.load("fake.pdf")

    assert len(rows) == 2
    assert rows[0]["topic"] == "2. Propuestas"
    assert rows[0]["subtopic"] == "2.1 Ley de Juventud"
    assert rows[0]["author"] == "Kilian Wirthwein, Javier Carbonell"


def test_tier2_skips_bibliography_section():
    bib_heading = _make_heading_item("Bibliografía", level=1)
    bib_text = _make_text_item("García, A. (2023). Voto joven en Europa. " * 5)
    loader = _make_loader_with_items([(bib_heading, 0), (bib_text, 0)])

    rows = loader.load("fake.pdf")

    assert len(rows) == 0


def test_tier2_appends_indicators_and_targets_to_text():
    proposals = [
        ExtractedProposal(
            text="El Estado debe invertir en investigacion y desarrollo tecnologico.",
            indicators=["% PIB en I+D"],
            targets=["3% del PIB para 2030"],
        )
    ]
    llm = _make_llm(proposals=proposals)

    prose = "El Estado debe invertir en investigacion y desarrollo tecnologico. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items([(_make_heading_item("Eje 1"), 0), (body, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert "Indicadores: % PIB en I+D" in rows[0]["text"]
    assert "Metas: 3% del PIB para 2030" in rows[0]["text"]


def test_reference_deduplication_across_sections():
    # LLM returns the same proposal twice (e.g. from resumen + detail)
    # _make_ref should disambiguate so all refs are unique
    proposals = [
        ExtractedProposal(text="La medida consiste en X. " * 3, title="Medida X"),
        ExtractedProposal(text="La medida consiste en X. " * 3, title="Medida X"),
    ]
    llm = _make_llm(proposals=proposals)

    prose = "La medida consiste en X. " * 5
    body = _make_text_item(prose)
    loader = _make_loader_with_items([(_make_heading_item("Propuestas"), 0), (body, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    assert len(rows) == 2
    refs = [r["reference"] for r in rows]
    assert len(set(refs)) == len(refs), "All references must be unique"


# ---------------------------------------------------------------------------
# Dedup by reference slug
# ---------------------------------------------------------------------------


def test_dedup_by_reference_keeps_first():
    rows = [
        {"reference": "abc", "text": "first"},
        {"reference": "abc", "text": "second"},
        {"reference": "xyz", "text": "third"},
    ]
    result = _dedup_by_reference(rows)
    assert len(result) == 2
    assert result[0]["text"] == "first"
    assert result[1]["text"] == "third"


def test_dedup_by_reference_no_duplicates_unchanged():
    rows = [{"reference": "a"}, {"reference": "b"}, {"reference": "c"}]
    result = _dedup_by_reference(rows)
    assert result == rows


def test_llm_extract_uses_topic_subtopic_from_response():
    proposals = [
        ExtractedProposal(
            text="El Estado debe garantizar el acceso a la vivienda para jovenes.",
            title="Medida 7",
            topic="3. Medidas economicas",
            subtopic="3.1.1.Vivienda",
        )
    ]
    llm = _make_llm(proposals=proposals)

    prose = "El Estado debe garantizar el acceso a la vivienda para jovenes. " * 3
    body = _make_text_item(prose)
    loader = _make_loader_with_items([(_make_heading_item("Some Heading"), 0), (body, 0)], llm=llm)

    rows = loader.load("fake.pdf")

    assert len(rows) == 1
    assert rows[0]["topic"] == "3. Medidas economicas"
    assert rows[0]["subtopic"] == "3.1.1.Vivienda"


# ---------------------------------------------------------------------------
# Real-file smoke tests (require LLM config + REPORT_INTEGRATION_TESTS=1)
# ---------------------------------------------------------------------------


@NEEDS_LLM
def test_real_v16_docx_extracts_tier1_rows():
    path = REAL_SAMPLES / "V16_Documento de consenso_ampliado.docx"
    loader = ReportLoader()
    rows = loader.load(str(path))
    # V16 has ~68-77 table rows; all should come from Tier 1 (no LLM on proposals)
    assert len(rows) >= 60, f"Expected ≥60 rows from V16, got {len(rows)}"
    topics = {r["topic"] for r in rows if r["topic"]}
    assert len(topics) >= 1
    assert all(r["author"] for r in rows)


@NEEDS_LLM
def test_real_juventud_pdf_extracts_16_medidas():
    path = REAL_SAMPLES / "La juventud pide paso.pdf"
    loader = ReportLoader()
    rows = loader.load(str(path))
    # Should find the 16 Medidas; LLM might find slightly more or fewer
    assert 12 <= len(rows) <= 25, f"Expected ~16 rows from La juventud, got {len(rows)}"
    # Author should be detected
    assert any("Wirthwein" in (r.get("author") or "") or "Carbonell" in (r.get("author") or "") for r in rows)


@NEEDS_LLM
def test_real_con_voz_pdf_extracts_20_propuestas():
    path = REAL_SAMPLES / "CON-VOZ-Y-VOTO.pdf"
    loader = ReportLoader()
    rows = loader.load(str(path))
    assert 15 <= len(rows) <= 30, f"Expected ~20 rows from CON-VOZ-Y-VOTO, got {len(rows)}"
    ejes = {r["topic"] for r in rows if r["topic"]}
    assert len(ejes) >= 3, "Expected proposals across multiple ejes"
