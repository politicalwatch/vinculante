import pytest

from vinculante.application.ingestion.spanish_legal_classifier import (
    ChunkClassification,
    classify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _heading(text: str, headings: list[str] | None = None) -> dict:
    return {
        "text": text,
        "text_markdown": "## " + text,
        "metadata": {
            "is_heading_only": True,
            "headings": headings or [],
            "dl_meta": {"doc_items": [{"label": "section_header"}]},
        },
    }


def _body(text: str, headings: list[str] | None = None, label: str = "text") -> dict:
    return {
        "text": text,
        "text_markdown": text,
        "metadata": {
            "is_heading_only": False,
            "headings": headings or [],
            "dl_meta": {"doc_items": [{"label": label}]},
        },
    }


# ---------------------------------------------------------------------------
# Heading-only chunk classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_type,expected_number", [
    ("Índice", "toc", None),
    ("INDICE", "toc", None),
    ("EXPOSICIÓN DE MOTIVOS", "exposicion_motivos", None),
    ("Exposición de Motivos", "exposicion_motivos", None),
    ("TÍTULO PRELIMINAR", "titulo", "PRELIMINAR"),
    ("Título I", "titulo", "I"),
    ("TÍTULO IV", "titulo", "IV"),
    ("CAPÍTULO I", "capitulo", None),
    ("Capítulo II", "capitulo", None),
    ("SECCIÓN 1", "seccion", None),
    ("Artículo 1.", "articulo", "1"),
    ("Artículo 23.", "articulo", "23"),
    ("Artículo 5 bis.", "articulo", "5 bis"),
    ("Disposición adicional primera.", "disp_adicional", "adicional primera"),
    ("Disposición transitoria única.", "disp_transitoria", "transitoria única"),
    ("Disposición derogatoria única.", "disp_derogatoria", "derogatoria única"),
    ("Disposición final primera.", "disp_final", "final primera"),
    ("Disposición final vigesimotercera.", "disp_final", "final vigesimotercera"),
    ("REY DE ESPAÑA", "preambulo", None),
    ("FELIPE VI", "preambulo", None),
    ("JUAN CARLOS I", "preambulo", None),
    ("Some random text", "unknown", None),
])
def test_heading_classification(text, expected_type, expected_number):
    [cl] = classify([_heading(text)])
    assert cl.section_type == expected_type
    assert cl.section_number == expected_number


# ---------------------------------------------------------------------------
# is_section_start rules for heading-only chunks
# ---------------------------------------------------------------------------

def test_heading_with_specific_type_is_section_start():
    [cl] = classify([_heading("Artículo 1.")])
    assert cl.is_section_start is True


def test_heading_unknown_is_not_section_start():
    [cl] = classify([_heading("Some generic heading")])
    assert cl.is_section_start is False


def test_toc_heading_is_section_start():
    [cl] = classify([_heading("Índice")])
    assert cl.is_section_start is True  # toc is specific (also skip=True)


# ---------------------------------------------------------------------------
# Matchability rules
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section_type,expected_matchable,expected_skip", [
    ("toc", False, True),
    ("preambulo", False, False),
    ("exposicion_motivos", False, False),
    ("titulo", False, False),
    ("capitulo", False, False),
    ("seccion", False, False),
    ("articulo", True, False),
    ("disp_adicional", True, False),
    ("disp_transitoria", False, False),
    ("disp_derogatoria", False, False),
    ("disp_final", False, False),
    ("unknown", True, False),
])
def test_matchability(section_type, expected_matchable, expected_skip):
    type_to_text = {
        "toc": "Índice",
        "preambulo": "REY DE ESPAÑA",
        "exposicion_motivos": "EXPOSICIÓN DE MOTIVOS",
        "titulo": "TÍTULO I",
        "capitulo": "CAPÍTULO I",
        "seccion": "SECCIÓN 1",
        "articulo": "Artículo 1.",
        "disp_adicional": "Disposición adicional primera.",
        "disp_transitoria": "Disposición transitoria única.",
        "disp_derogatoria": "Disposición derogatoria única.",
        "disp_final": "Disposición final primera.",
        "unknown": "Random heading text",
    }
    [cl] = classify([_heading(type_to_text[section_type])])
    assert cl.is_matchable == expected_matchable
    assert cl.skip == expected_skip


# ---------------------------------------------------------------------------
# Body chunk classification via headings context
# ---------------------------------------------------------------------------

def test_body_under_articulo_is_matchable():
    chunk = _body("El artículo regula...", headings=["TÍTULO I", "Artículo 5. Objeto."])
    [cl] = classify([chunk])
    assert cl.section_type == "articulo"
    assert cl.is_matchable is True


def test_body_under_titulo_is_unknown_matchable():
    # No article heading detected — falls back to fail-open unknown → matchable
    chunk = _body("Texto del artículo...", headings=["TÍTULO PRELIMINAR"])
    [cl] = classify([chunk])
    assert cl.section_type == "unknown"
    assert cl.is_matchable is True


def test_body_under_capitulo_is_unknown_matchable():
    chunk = _body("Contenido...", headings=["TÍTULO I", "CAPÍTULO II"])
    [cl] = classify([chunk])
    assert cl.section_type == "unknown"
    assert cl.is_matchable is True


def test_body_under_disp_final_is_not_matchable():
    chunk = _body("Modifícase la Ley...", headings=["Disposición final primera."])
    [cl] = classify([chunk])
    assert cl.section_type == "disp_final"
    assert cl.is_matchable is False
    assert cl.skip is False


def test_body_under_disp_adicional_is_matchable():
    chunk = _body("Esta disposición...", headings=["Disposición adicional primera."])
    [cl] = classify([chunk])
    assert cl.section_type == "disp_adicional"
    assert cl.is_matchable is True


def test_body_under_exposicion_is_not_matchable():
    chunk = _body("La presente ley...", headings=["EXPOSICIÓN DE MOTIVOS"])
    [cl] = classify([chunk])
    assert cl.section_type == "exposicion_motivos"
    assert cl.is_matchable is False


def test_body_with_no_headings_is_unknown_matchable():
    chunk = _body("Algún contenido.", headings=[])
    [cl] = classify([chunk])
    assert cl.section_type == "unknown"
    assert cl.is_matchable is True


# ---------------------------------------------------------------------------
# is_section_start for body chunks — direct vs heading-context vs propagation
# ---------------------------------------------------------------------------

def test_direct_match_body_is_section_start():
    # "EXPOSICIÓN DE MOTIVOS" body chunk (as emitted in styleless .docx)
    chunk = _body("EXPOSICIÓN DE MOTIVOS", headings=[])
    [cl] = classify([chunk])
    assert cl.section_type == "exposicion_motivos"
    assert cl.is_section_start is True


def test_heading_context_first_body_is_section_start():
    # First body under an article (tracker has no context yet)
    chunk = _body("El artículo establece...", headings=["Artículo 3. Ámbito."])
    [cl] = classify([chunk])
    assert cl.is_section_start is True


def test_heading_context_second_body_same_section_is_not_start():
    # Two body chunks under the same article heading — second should not restart
    chunks = [
        _body("Primer párrafo.", headings=["Artículo 3."]),
        _body("Segundo párrafo.", headings=["Artículo 3."]),
    ]
    result = classify(chunks)
    assert result[0].is_section_start is True
    assert result[1].is_section_start is False


def test_propagation_body_is_not_section_start():
    # After exposicion heading, body chunks propagate but don't start new sections
    chunks = [
        _heading("EXPOSICIÓN DE MOTIVOS"),
        _body("Párrafo 1.", headings=[]),
        _body("Párrafo 2.", headings=[]),
    ]
    result = classify(chunks)
    assert result[0].is_section_start is True
    assert result[1].is_section_start is False
    assert result[2].is_section_start is False


def test_unknown_body_is_not_section_start():
    chunk = _body("Algún contenido.", headings=[])
    [cl] = classify([chunk])
    assert cl.is_section_start is False


# ---------------------------------------------------------------------------
# TOC region: body chunks with list_item label inside TOC get hard-skipped
# ---------------------------------------------------------------------------

def test_toc_body_chunks_are_hard_skipped():
    chunks = [
        _heading("Índice"),
        _body("- **Exposición de motivos**\n- **Título I...**", label="list_item"),
        _body("- **Disposiciones finales**", label="list_item"),
    ]
    result = classify(chunks)
    assert result[0].section_type == "toc"
    assert result[0].skip is True
    assert result[1].section_type == "toc"
    assert result[1].skip is True
    assert result[2].section_type == "toc"
    assert result[2].skip is True


def test_toc_region_ends_on_non_list_item_body():
    chunks = [
        _heading("Índice"),
        _body("- **Título I...**", label="list_item"),  # TOC entry → skip
        _body("EXPOSICIÓN DE MOTIVOS", label="text"),   # real content → exits TOC
        _body("body of exposicion", label="text"),
    ]
    result = classify(chunks)
    assert result[0].skip is True   # Índice heading
    assert result[1].skip is True   # list_item TOC entry
    assert result[2].skip is False  # exits TOC; exposicion_motivos → non-matchable
    assert result[2].section_type == "exposicion_motivos"
    assert result[3].section_type == "exposicion_motivos"  # inherited via context
    assert result[3].is_matchable is False


def test_toc_region_ends_on_structural_heading():
    chunks = [
        _heading("Índice"),
        _body("- **Título I...**", label="list_item"),  # TOC entry → skip
        _heading("TÍTULO I"),                           # heading exits TOC
        _body("body text", headings=["TÍTULO I"]),
    ]
    result = classify(chunks)
    assert result[0].skip is True   # Índice heading
    assert result[1].skip is True   # TOC body entry
    assert result[2].skip is False  # TÍTULO I heading (non-matchable, not skipped)
    assert result[2].section_type == "titulo"
    assert result[3].section_type == "unknown"  # body under titulo → fail-open
    assert result[3].is_matchable is True


# ---------------------------------------------------------------------------
# Disposiciones region: "Artículo N." headings are false positives
# ---------------------------------------------------------------------------

def test_articulo_heading_inside_disp_final_merges_into_parent():
    """Articles inside disposiciones finales modify another law — they belong to the
    parent disposición, not their own section."""
    chunks = [
        _heading("Artículo 1."),                       # main articulado → matchable
        _heading("Disposición final primera."),        # → disposiciones region
        _heading("Artículo 10."),                      # inside disp_final → merges in
    ]
    result = classify(chunks)
    assert result[0].section_type == "articulo"
    assert result[0].is_matchable is True
    assert result[1].section_type == "disp_final"
    assert result[1].is_matchable is False
    # Artículo 10 inherits parent disp_final context, not a new boundary
    assert result[2].section_type == "disp_final"
    assert result[2].section_number == "final primera"
    assert result[2].is_matchable is False
    assert result[2].is_section_start is False


def test_disp_adicional_before_other_disposiciones_is_matchable():
    chunks = [
        _heading("Disposición adicional primera."),
        _body("El Gobierno podrá...", headings=["Disposición adicional primera."]),
        _heading("Disposición derogatoria única."),
        _heading("Disposición final primera."),
    ]
    result = classify(chunks)
    assert result[0].section_type == "disp_adicional"
    assert result[0].is_matchable is True
    assert result[1].section_type == "disp_adicional"
    assert result[1].is_matchable is True
    assert result[2].section_type == "disp_derogatoria"
    assert result[2].is_matchable is False
    assert result[3].section_type == "disp_final"
    assert result[3].is_matchable is False


# ---------------------------------------------------------------------------
# Section number extraction
# ---------------------------------------------------------------------------

def test_section_number_extracted_for_articulo():
    [cl] = classify([_heading("Artículo 42.")])
    assert cl.section_number == "42"


def test_section_number_extracted_for_articulo_bis():
    [cl] = classify([_heading("Artículo 2 bis.")])
    assert cl.section_number == "2 bis"


def test_section_number_extracted_for_titulo():
    [cl] = classify([_heading("TÍTULO PRELIMINAR")])
    assert cl.section_number == "PRELIMINAR"


def test_section_number_extracted_for_disp():
    [cl] = classify([_heading("Disposición final decimotercera.")])
    assert cl.section_number == "final decimotercera"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_chunks_returns_empty():
    assert classify([]) == []


def test_output_length_matches_input():
    chunks = [_heading("Artículo 1."), _body("text"), _heading("Índice")]
    assert len(classify(chunks)) == 3


def test_preambulo_body_via_text_fallback():
    # Preamble content where chunk text starts with the marker
    chunk = _body("REY DE ESPAÑA\nA todos los que la presente vieren...", headings=[])
    [cl] = classify([chunk])
    assert cl.section_type == "preambulo"
    assert cl.is_matchable is False


# ---------------------------------------------------------------------------
# Context propagation — articulo and disp_adicional now propagate
# ---------------------------------------------------------------------------

def test_body_inside_articulo_inherits_articulo():
    # Body chunks under an article inherit its type and number (all matchable)
    chunks = [
        _heading("Artículo 5."),
        _body("Los poderes públicos promoverán...", headings=[]),
        _body("En particular se garantizará...", headings=[]),
    ]
    result = classify(chunks)
    assert result[0].section_type == "articulo"
    assert result[0].section_number == "5"
    assert result[0].is_matchable is True
    assert result[1].section_type == "articulo"
    assert result[1].section_number == "5"
    assert result[1].is_matchable is True
    assert result[2].section_type == "articulo"
    assert result[2].is_matchable is True


def test_body_inside_disp_adicional_inherits_disp_adicional():
    chunks = [
        _heading("Disposición adicional primera."),
        _body("El Gobierno adoptará las medidas...", headings=[]),
    ]
    result = classify(chunks)
    assert result[1].section_type == "disp_adicional"
    assert result[1].section_number == "adicional primera"
    assert result[1].is_matchable is True


def test_section_number_propagates_to_unknown_body():
    chunks = [
        _heading("Artículo 5."),
        _body("Fines de la actuación...", headings=[]),
    ]
    result = classify(chunks)
    assert result[1].section_number == "5"


def test_unknown_body_inherits_exposicion_motivos_context():
    chunks = [
        _heading("EXPOSICIÓN DE MOTIVOS"),
        _body("El artículo 48 de la Constitución Española...", headings=[]),
        _body("En este marco, la Convención...", headings=[]),
    ]
    result = classify(chunks)
    assert result[0].section_type == "exposicion_motivos"
    assert result[0].is_matchable is False
    assert result[1].section_type == "exposicion_motivos"
    assert result[1].is_matchable is False
    assert result[2].section_type == "exposicion_motivos"
    assert result[2].is_matchable is False


def test_unknown_body_inherits_disp_final_context():
    chunks = [
        _heading("Disposición final primera."),
        _body("Modifícase la Ley 30/1992...", headings=[]),
        _body("Uno. El artículo 5 queda redactado...", headings=[]),
    ]
    result = classify(chunks)
    assert result[1].section_type == "disp_final"
    assert result[1].is_matchable is False
    assert result[2].section_type == "disp_final"
    assert result[2].is_matchable is False


def test_context_resets_at_titulo_body_stays_unknown():
    # titulo is in CONTEXT_RESET: body after it is unknown (fail-open matchable)
    chunks = [
        _heading("TÍTULO I"),
        _body("Actuación de los poderes públicos", headings=[]),
    ]
    result = classify(chunks)
    assert result[1].section_type == "unknown"
    assert result[1].is_matchable is True


def test_context_resets_at_new_article():
    # After an exposición, a new article resets context; body inherits article
    chunks = [
        _heading("EXPOSICIÓN DE MOTIVOS"),
        _body("Exposición body...", headings=[]),
        _heading("Artículo 1."),
        _body("Artículo body...", headings=[]),
    ]
    result = classify(chunks)
    assert result[1].section_type == "exposicion_motivos"  # inherited
    assert result[3].section_type == "articulo"            # propagated from article
    assert result[3].is_matchable is True


def test_preambulo_context_propagates_before_exposicion():
    chunks = [
        _body("REY DE ESPAÑA", headings=[]),                    # direct match
        _body("A todos los que la presente vieren...", headings=[]),
        _body("Sabed: Que las Cortes...", headings=[]),
        _body("EXPOSICIÓN DE MOTIVOS", headings=[]),             # new section
        _body("El artículo 48...", headings=[]),
    ]
    result = classify(chunks)
    assert result[0].section_type == "preambulo"
    assert result[0].is_matchable is False
    assert result[1].section_type == "preambulo"   # inherited
    assert result[2].section_type == "preambulo"   # inherited
    assert result[3].section_type == "exposicion_motivos"
    assert result[4].section_type == "exposicion_motivos"  # inherited


# ---------------------------------------------------------------------------
# Felipe VI preamble detection
# ---------------------------------------------------------------------------

def test_felipe_body_chunk_starts_preambulo():
    chunk = _body("FELIPE VI", headings=[])
    [cl] = classify([chunk])
    assert cl.section_type == "preambulo"
    assert cl.is_section_start is True
    assert cl.is_matchable is False


def test_preambulo_group_felipe_through_sabed():
    # Full preamble sequence: FELIPE VI → boundary, rest propagates
    chunks = [
        _body("FELIPE VI", headings=[]),
        _body("REY DE ESPAÑA", headings=[]),
        _body("A todos los que la presente vieren y entendieren.", headings=[]),
        _body("Sabed: Que las Cortes...", headings=[]),
    ]
    result = classify(chunks)
    assert result[0].section_type == "preambulo"
    assert result[0].is_section_start is True
    # REY DE ESPAÑA direct-matches preambulo but same context → not a new start
    assert result[1].section_type == "preambulo"
    assert result[1].is_section_start is False
    assert result[2].section_type == "preambulo"
    assert result[3].section_type == "preambulo"


# ---------------------------------------------------------------------------
# Separator hard-skip
# ---------------------------------------------------------------------------

def test_dash_separator_is_hard_skipped():
    [cl] = classify([_body("------------------------")])
    assert cl.section_type == "separator"
    assert cl.skip is True
    assert cl.is_matchable is False


def test_underscore_and_equals_separators_skipped():
    chunks = [_body("____"), _body("====")]
    result = classify(chunks)
    assert all(cl.skip for cl in result)
    assert all(cl.section_type == "separator" for cl in result)


def test_asterisk_separator_skipped():
    [cl] = classify([_body("***")])
    assert cl.skip is True
    assert cl.section_type == "separator"


def test_short_dashes_not_separator():
    [cl] = classify([_body("--")])
    assert cl.section_type == "unknown"
    assert cl.skip is False


def test_separator_does_not_reset_article_context():
    chunks = [
        _heading("Artículo 5."),
        _body("Primer párrafo.", headings=[]),
        _body("------------------------", headings=[]),
        _body("Segundo párrafo.", headings=[]),
    ]
    result = classify(chunks)
    # Separator is skipped but should not reset articulo context
    assert result[2].skip is True
    assert result[3].section_type == "articulo"
    assert result[3].is_matchable is True
    assert result[3].is_section_start is False


# ---------------------------------------------------------------------------
# disp_* inside later disp_* merges into parent
# ---------------------------------------------------------------------------

def test_disp_adicional_heading_inside_disp_final_merges_into_parent():
    """disp_adicional reference inside a disp_final should be absorbed."""
    chunks = [
        _heading("Disposición final primera."),
        _body("Modifícase la Ley X.", headings=[]),
        _heading("Disposición adicional segunda."),
        _body("El nuevo texto queda redactado.", headings=[]),
    ]
    result = classify(chunks)
    for cl in result:
        assert cl.section_type == "disp_final"
        assert cl.section_number == "final primera"
        assert cl.is_matchable is False
    assert result[0].is_section_start is True
    assert result[1].is_section_start is False
    assert result[2].is_section_start is False
    assert result[3].is_section_start is False


def test_disp_transitoria_heading_inside_disp_final_merges():
    """disp_transitoria reference inside a disp_final should be absorbed."""
    chunks = [
        _heading("Disposición final primera."),
        _body("Se modifica la Ley.", headings=[]),
        _heading("Disposición transitoria única."),
        _body("En tanto no se desarrolle reglamentariamente.", headings=[]),
    ]
    result = classify(chunks)
    for cl in result:
        assert cl.section_type == "disp_final"
        assert cl.section_number == "final primera"
    assert result[2].is_section_start is False


def test_consecutive_disp_adicional_remain_separate():
    """Two genuine disp_adicional headings in sequence each start a new section."""
    chunks = [
        _heading("Disposición adicional primera."),
        _heading("Disposición adicional segunda."),
    ]
    result = classify(chunks)
    assert result[0].section_type == "disp_adicional"
    assert result[0].section_number == "adicional primera"
    assert result[0].is_section_start is True
    assert result[1].section_type == "disp_adicional"
    assert result[1].section_number == "adicional segunda"
    assert result[1].is_section_start is True


def test_disp_final_after_disp_adicional_still_starts_new_section():
    """disp_final has higher order than disp_adicional — must not be absorbed."""
    chunks = [
        _heading("Disposición adicional primera."),
        _heading("Disposición final primera."),
    ]
    result = classify(chunks)
    assert result[0].section_type == "disp_adicional"
    assert result[0].is_section_start is True
    assert result[1].section_type == "disp_final"
    assert result[1].is_section_start is True
