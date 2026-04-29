from vinculante.infrastructure.chunking.docling_chunker import _split_merged_heading


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
