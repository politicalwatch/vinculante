import pytest
from unittest.mock import MagicMock

from vinculante.infrastructure.chunking.docling_chunker import (
    _split_merged_heading,
    _strip_inline_md,
    _normalize_line,
    _detect_furniture,
    _strip_phrase,
    _apply_furniture_strip,
)
from docling_core.types.doc.document import ContentLayer


def test_splits_title_from_chapter_heading():
    text = "Ley de Cambio Climático y Transición Energética Capítulo I: Disposiciones Generales"
    assert _split_merged_heading(text) == [
        "Ley de Cambio Climático y Transición Energética",
        "Capítulo I: Disposiciones Generales",
    ]


def test_keeps_single_heading_intact():
    assert _split_merged_heading("Capítulo II: Energías Renovables") == [
        "Capítulo II: Energías Renovables",
    ]


def test_splits_multiple_legal_keywords():
    text = "Título I: Preliminar Capítulo I: Objeto Sección 1: Definiciones"
    assert _split_merged_heading(text) == [
        "Título I: Preliminar",
        "Capítulo I: Objeto",
        "Sección 1: Definiciones",
    ]


def test_does_not_split_when_keyword_is_at_start():
    assert _split_merged_heading("Disposición transitoria primera") == [
        "Disposición transitoria primera",
    ]


def test_strips_whitespace_and_drops_empty():
    assert _split_merged_heading("   Capítulo I   ") == ["Capítulo I"]


# ---------------------------------------------------------------------------
# _strip_inline_md
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("inp,expected", [
    ("**bold**", "bold"),
    ("*italic*", "italic"),
    ("__under__", "under"),
    ("_single_", "single"),
    ("Plain text", "Plain text"),
    ("Mixed **a** and *b*", "Mixed a and b"),
    ("No markers here", "No markers here"),
])
def test_strip_inline_md(inp, expected):
    assert _strip_inline_md(inp) == expected


# ---------------------------------------------------------------------------
# _normalize_line
# ---------------------------------------------------------------------------

def test_normalize_line_casefolds_and_strips():
    assert _normalize_line("  BOLETÍN OFICIAL  ") == "boletin oficial"


def test_normalize_line_collapses_whitespace():
    assert _normalize_line("Serie   A") == "serie a"


def test_normalize_line_removes_combining():
    assert _normalize_line("Núm. 52-1") == "num. 52-1"


# ---------------------------------------------------------------------------
# _strip_phrase
# ---------------------------------------------------------------------------

def test_strip_phrase_removes_exact():
    assert _strip_phrase("texto del Pág. 19\n\nContinua.", "Pág. 19") == "texto del \n\nContinua."


def test_strip_phrase_flexible_whitespace():
    assert "Serie A" not in _strip_phrase("foo Serie  A bar", "Serie A")


def test_strip_phrase_empty_phrase_returns_unchanged():
    assert _strip_phrase("foo bar", "") == "foo bar"


# ---------------------------------------------------------------------------
# helpers for _detect_furniture tests
# ---------------------------------------------------------------------------

def _make_bbox(t, b, H, coord_origin="TOPLEFT"):
    bbox = MagicMock()
    # to_top_left_origin returns a bbox-like object with t and b
    tl_bbox = MagicMock()
    tl_bbox.t = t
    tl_bbox.b = b
    bbox.to_top_left_origin.return_value = tl_bbox
    return bbox


def _make_item(
    text,
    page_no,
    label="text",
    content_layer=ContentLayer.BODY,
    self_ref=None,
    bbox=None,
):
    item = MagicMock()
    item.text = text
    item.label = label
    item.content_layer = content_layer
    item.self_ref = self_ref or f"#/{page_no}/{text[:8]}"
    prov_entry = MagicMock()
    prov_entry.page_no = page_no
    prov_entry.bbox = bbox
    item.prov = [prov_entry]
    return item


def _make_dl_doc(items, num_pages, page_height=1000.0):
    doc = MagicMock()
    doc.num_pages.return_value = num_pages
    doc.iterate_items.return_value = [(item, 0) for item in items]
    page_mock = MagicMock()
    page_mock.size.height = page_height
    doc.pages = {pg: page_mock for pg in range(1, num_pages + 1)}
    return doc


# ---------------------------------------------------------------------------
# _detect_furniture — text-repetition (backward compat with previous tests)
# ---------------------------------------------------------------------------

def test_detects_repeated_lines_as_furniture():
    items = [
        _make_item("BOLETÍN OFICIAL DE LAS CORTES GENERALES", pg) for pg in range(1, 5)
    ] + [
        _make_item("Este artículo establece obligaciones.", pg) for pg in range(1, 3)
    ]
    doc = _make_dl_doc(items, num_pages=10)
    m = _detect_furniture(doc)
    assert "boletin oficial de las cortes generales" in m.lines
    assert "este articulo establece obligaciones." not in m.lines


def test_auto_includes_page_header_label():
    items = [_make_item("Pág. 5", 5, label="page_header")]
    doc = _make_dl_doc(items, num_pages=2)
    m = _detect_furniture(doc)
    assert "pag. 5" in m.lines


def test_auto_includes_furniture_content_layer():
    items = [_make_item("Serie A", 3, content_layer=ContentLayer.FURNITURE)]
    doc = _make_dl_doc(items, num_pages=2)
    m = _detect_furniture(doc)
    assert "serie a" in m.lines


def test_skips_detection_below_min_pages():
    items = [_make_item("Texto normal en varias páginas", pg) for pg in range(1, 3)]
    doc = _make_dl_doc(items, num_pages=2)
    m = _detect_furniture(doc)
    assert "texto normal en varias paginas" not in m.lines


def test_does_not_mark_list_markers_as_furniture():
    items = [_make_item("a) Primera opción disponible aquí", pg) for pg in range(1, 8)]
    doc = _make_dl_doc(items, num_pages=10)
    m = _detect_furniture(doc)
    assert "a) primera opcion disponible aqui" not in m.lines


def test_does_not_mark_short_lines_as_furniture():
    items = [_make_item("§", pg) for pg in range(1, 10)]
    doc = _make_dl_doc(items, num_pages=10)
    m = _detect_furniture(doc)
    assert not any(len(f) < 6 for f in m.lines)


# ---------------------------------------------------------------------------
# _detect_furniture — bbox-zone detection
# ---------------------------------------------------------------------------

def _header_bbox(H=1000.0):
    """Item whose top sits at 3% of page height (header zone)."""
    return _make_bbox(t=H * 0.03, b=H * 0.07, H=H)


def _body_bbox(H=1000.0):
    """Item whose top sits at 20% of page height (body zone)."""
    return _make_bbox(t=H * 0.20, b=H * 0.25, H=H)


def test_bbox_zone_detects_varying_page_numbers():
    H = 1000.0
    # "Pág. N" varies per page — text-repetition won't catch it, but bbox will
    items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert all(f"#/pag{pg}" in m.refs for pg in range(1, 11))


def test_bbox_zone_adds_phrases_for_ref_stripping():
    H = 1000.0
    items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert m.phrases["#/pag5"] == "Pág. 5"


def test_bbox_zone_requires_threshold_pages():
    H = 1000.0
    # Only 1 page has a header-zone item → below threshold (need ≥ 2 for a 5-page doc)
    items = [
        _make_item("Pág. 1", 1, self_ref="#/pag1", bbox=_header_bbox(H)),
        *[_make_item("Cuerpo del texto legal.", pg, bbox=_body_bbox(H)) for pg in range(1, 6)],
    ]
    doc = _make_dl_doc(items, num_pages=5, page_height=H)
    m = _detect_furniture(doc)
    assert "#/pag1" not in m.refs


def test_bbox_zone_catches_items_at_nine_percent():
    H = 1000.0
    # Items at top_pct = 0.09 — above old 0.08 threshold, below new 0.12 threshold
    items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_make_bbox(t=H * 0.09, b=H * 0.11, H=H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert all(f"#/pag{pg}" in m.refs for pg in range(1, 11))


def test_bbox_zone_does_not_strip_body_near_page_bottom():
    H = 1000.0
    # Header furniture confirms the zone; body item at b=0.92H must not get marked.
    header_items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    body_ref = "#/body_bottom"
    body_item = _make_item(
        "Texto cuerpo al final de la página.",
        5,
        self_ref=body_ref,
        bbox=_make_bbox(t=H * 0.85, b=H * 0.92, H=H),
    )
    doc = _make_dl_doc(header_items + [body_item], num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert body_ref not in m.refs


def test_bbox_zone_not_triggered_for_body_position():
    H = 1000.0
    # Same text on many pages but in body position — should not be marked furniture
    items = [
        _make_item("Obligaciones generales del fabricante.", pg, bbox=_body_bbox(H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert all(item.self_ref not in m.refs for item in items)


def test_bbox_zone_does_not_strip_unique_body_line_in_header_zone():
    H = 1000.0
    # Pages 1-10: "Pág. N" furniture in header zone → zone confirmed, template built.
    # Page 5 additionally has a unique long body sentence at the very top of the page
    # (e.g. start of item 5, whose bbox lands in header zone due to page break position).
    # That unique sentence must NOT be stripped.
    pag_items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    unique_text = (
        "5. La Secretaría de Estado de Telecomunicaciones e Infraestructuras "
        "Digitales ejercerá las funciones de vigilancia, supervisión y control "
        "de los requisitos y condiciones establecidos en los apartados anteriores."
    )
    unique_ref = "#/secretaria"
    unique_item = _make_item(unique_text, 5, self_ref=unique_ref, bbox=_header_bbox(H))
    doc = _make_dl_doc(pag_items + [unique_item], num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    # "Pág. N" template must still be detected
    assert any(pat.search("Pág. 19") for pat in m.templates)
    # The unique body line must not be furniture
    assert unique_ref not in m.refs
    assert _normalize_line(unique_text) not in m.lines


def test_bbox_zone_substring_promotes_separate_columns_of_joined_phrase():
    """Zone items whose text is a substring of a confirmed joined phrase are promoted.

    Mirrors real PDF behaviour: "Serie A Núm. 52-1" is one DocItem on 12 pages,
    but on 3 other pages Docling emits "Serie A" and "Núm. 52-1" as separate
    DocItems. The standalones must be promoted via substring containment so they
    don't leak into body chunks.
    """
    H = 1000.0
    # 12 pages with joined phrase → multi-page-confirmed
    joined_items = [
        _make_item("Serie A Núm. 52-1", pg, self_ref=f"#/joined{pg}", bbox=_header_bbox(H))
        for pg in range(1, 13)
    ]
    # 3 pages with standalone "Serie A"
    serie_items = [
        _make_item("Serie A", 12 + i, self_ref=f"#/serie{i}", bbox=_header_bbox(H))
        for i in range(1, 4)
    ]
    # 3 pages with standalone "Núm. 52-1"
    num_items = [
        _make_item("Núm. 52-1", 12 + i, self_ref=f"#/num{i}", bbox=_header_bbox(H))
        for i in range(1, 4)
    ]
    total_pages = 15
    doc = _make_dl_doc(joined_items + serie_items + num_items, num_pages=total_pages, page_height=H)
    m = _detect_furniture(doc)

    # Joined phrase confirmed
    assert "serie a num. 52-1" in m.lines
    # Standalone substrings must also be promoted
    assert "serie a" in m.lines
    assert "num. 52-1" in m.lines
    for item in serie_items:
        assert item.self_ref in m.refs
    for item in num_items:
        assert item.self_ref in m.refs


# ---------------------------------------------------------------------------
# _detect_furniture — template generalization
# ---------------------------------------------------------------------------

def test_detect_furniture_builds_template_for_repeated_numeric_pattern():
    H = 1000.0
    # 10 pages each with "Pág. N" in header zone → template "Pág. \d+" built
    items = [
        _make_item(f"Pág. {pg}", pg, self_ref=f"#/pag{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert len(m.templates) >= 1
    assert any(pat.search("Pág. 19") for pat in m.templates)


def test_detect_furniture_template_does_not_include_long_literal_phrases():
    H = 1000.0
    # "11 de abril de 2025" has long literals → should NOT produce a template
    items = [
        _make_item(f"11 de abril de {2000 + pg}", pg, self_ref=f"#/date{pg}", bbox=_header_bbox(H))
        for pg in range(1, 11)
    ]
    doc = _make_dl_doc(items, num_pages=10, page_height=H)
    m = _detect_furniture(doc)
    assert not any(pat.search("11 de abril de 2025") for pat in m.templates)


# ---------------------------------------------------------------------------
# _apply_furniture_strip — template stripping
# ---------------------------------------------------------------------------

def test_apply_furniture_strips_via_template_when_not_in_phrases():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    # "Pág. 19" is fused into body text — NOT a separate ref/phrase
    ref = "#/pag18"
    import re
    m = _FurnitureMatchers(
        lines=set(),
        refs={ref},
        phrases={ref: "Pág. 18"},
        templates=[re.compile(r"Pág\.\s*\d+", re.IGNORECASE)],
    )
    # doc_items owns "#/pag18" but NOT "#/pag19"; text contains both
    di = MagicMock()
    di.self_ref = ref

    text = "artículo 56 de la Ley 39/2015, de 1 de octubre, del Pág. 19\n\nProcedimiento."
    result = _apply_furniture_strip(text, m, [di])
    assert "Pág. 19" not in result
    assert "Procedimiento." in result


# ---------------------------------------------------------------------------
# _apply_furniture_strip
# ---------------------------------------------------------------------------

def test_apply_furniture_strips_inline_phrase():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    ref = "#/pag19"
    m = _FurnitureMatchers(
        lines=set(),
        refs={ref},
        phrases={ref: "Pág. 19"},
    )
    di = MagicMock()
    di.self_ref = ref
    di.text = "Pág. 19"

    text = "texto del artículo 56 de la Ley, del Pág. 19\n\nProcedimiento Administrativo."
    result = _apply_furniture_strip(text, m, [di])
    assert "Pág. 19" not in result
    assert "Procedimiento Administrativo" in result


def test_apply_furniture_strips_inline_phrase_without_owning_ref():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    ref = "#/pag19"
    m = _FurnitureMatchers(
        lines=set(),
        refs={ref},
        phrases={ref: "Pág. 19"},
    )
    # doc_items does NOT contain the furniture ref — different chunk owns it
    other_di = MagicMock()
    other_di.self_ref = "#/some_other_item"

    text = "de 1 de octubre, del Pág. 19\n\nProcedimiento Administrativo Común."
    result = _apply_furniture_strip(text, m, [other_di])
    assert "Pág. 19" not in result
    assert "Procedimiento Administrativo Común" in result


def test_apply_furniture_strips_standalone_lines():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    m = _FurnitureMatchers(lines={"serie a", "num. 52-1"})
    text = "Artículo 4.\n\nSerie A\n\nNúm. 52-1\n\nTexto del artículo."
    result = _apply_furniture_strip(text, m, [])
    assert "Serie A" not in result
    assert "Núm. 52-1" not in result
    assert "Artículo 4." in result
    assert "Texto del artículo." in result


def test_apply_furniture_collapses_multiple_newlines():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    m = _FurnitureMatchers(lines={"pagina 1"})
    text = "Párrafo uno.\n\n\n\nPágina 1\n\n\n\nPárrafo dos."
    result = _apply_furniture_strip(text, m, [])
    assert "\n\n\n" not in result


def test_apply_furniture_returns_empty_when_all_stripped():
    from vinculante.infrastructure.chunking.docling_chunker import _FurnitureMatchers

    m = _FurnitureMatchers(lines={"solo furniture"})
    result = _apply_furniture_strip("Solo furniture", m, [])
    assert result == ""
