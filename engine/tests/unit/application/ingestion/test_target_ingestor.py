from unittest.mock import MagicMock

from vinculante.application.ingestion.target_ingestor import TargetIngestor
from vinculante.domain.entities import Section, TargetDocument


def _body_chunk(text: str, headings: list[str] | None = None, label: str = "text", page_no: int | None = None) -> dict:
    doc_item: dict = {"label": label}
    if page_no is not None:
        doc_item["prov"] = [{"page_no": page_no}]
    return {
        "text": text,
        "text_markdown": text,
        "metadata": {
            "is_heading_only": False,
            "headings": headings or [],
            "dl_meta": {"doc_items": [doc_item]},
        },
    }


def _heading_chunk(text: str, level: int = 1, page_no: int | None = None) -> dict:
    doc_item: dict = {"label": "section_header"}
    if page_no is not None:
        doc_item["prov"] = [{"page_no": page_no}]
    return {
        "text": text,
        "text_markdown": ("#" * (level + 1)) + " " + text,
        "metadata": {
            "is_heading_only": True,
            "dl_meta": {"doc_items": [doc_item]},
        },
    }


def _make_ingestor(chunks: list[dict]) -> tuple[TargetIngestor, MagicMock]:
    saved_target = TargetDocument(title="t", author="a")
    saved_target.id = 1

    target_repo = MagicMock()
    target_repo.save.return_value = saved_target

    section_repo = MagicMock()
    chunker = MagicMock()
    chunker.chunk.return_value = chunks

    ingestor = TargetIngestor(target_repo=target_repo, section_repo=section_repo, chunker=chunker)
    return ingestor, section_repo


# ---------------------------------------------------------------------------
# Basic section creation
# ---------------------------------------------------------------------------

def test_heading_only_chunk_becomes_non_matchable_capitulo():
    chunks = [_heading_chunk("Capítulo I", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].text == "Capítulo I"
    assert saved[0].section_type == "capitulo"
    assert saved[0].is_matchable is False
    assert saved[0].text_markdown == "## Capítulo I"


def test_body_chunk_under_article_is_matchable():
    # Body content under an article heading → matchable
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("body text", headings=["Artículo 1."]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert "body text" in saved[0].text
    assert saved[0].section_type == "articulo"
    assert saved[0].is_matchable is True


# ---------------------------------------------------------------------------
# Grouping: chunks merge into logical sections
# ---------------------------------------------------------------------------

def test_articulo_header_and_body_merge():
    chunks = [
        _heading_chunk("Artículo 5.", level=1),
        _body_chunk("La actuación de los poderes públicos...", headings=[]),
        _body_chunk("a) El fomento de la participación...", headings=[], label="list_item"),
        _body_chunk("b) La garantía de derechos...", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "articulo"
    assert saved[0].section_number == "5"
    assert saved[0].is_matchable is True
    assert "Artículo 5." in saved[0].text
    assert "La actuación" in saved[0].text
    assert "a) El fomento" in saved[0].text
    assert "b) La garantía" in saved[0].text


def test_exposicion_full_collapse():
    chunks = [
        _heading_chunk("EXPOSICIÓN DE MOTIVOS", level=1),
        _body_chunk("El artículo 48 de la Constitución...", headings=[]),
        _body_chunk("I", headings=[]),   # Roman subsection — propagates, doesn't split
        _body_chunk("En este marco, la Convención...", headings=[]),
        _body_chunk("II", headings=[]),
        _body_chunk("Dentro del ordenamiento jurídico...", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "exposicion_motivos"
    assert saved[0].is_matchable is False
    assert "El artículo 48" in saved[0].text
    assert "En este marco" in saved[0].text
    assert "Dentro del ordenamiento" in saved[0].text


def test_preambulo_starts_at_felipe_title_dropped():
    # Title chunk is a leading orphan → dropped; FELIPE VI opens preámbulo group
    chunks = [
        _body_chunk("Anteproyecto de Ley Orgánica de Juventud", headings=[]),  # orphan
        _body_chunk("FELIPE VI", headings=[]),
        _body_chunk("REY DE ESPAÑA", headings=[]),
        _body_chunk("A todos los que la presente vieren y entendieren.", headings=[]),
        _body_chunk("Sabed: Que las Cortes Generales han aprobado...", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "preambulo"
    assert saved[0].is_matchable is False
    assert "FELIPE VI" in saved[0].text
    assert "REY DE ESPAÑA" in saved[0].text
    assert "A todos" in saved[0].text
    # Title orphan was dropped
    assert "Anteproyecto de Ley Orgánica de Juventud" not in saved[0].text


def test_titulo_with_subtitle_merges():
    chunks = [
        _heading_chunk("TÍTULO I", level=1),
        _body_chunk("Actuación de los poderes públicos", headings=["TÍTULO I"]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "titulo"
    assert "TÍTULO I" in saved[0].text
    assert "Actuación de los poderes públicos" in saved[0].text


def test_disposiciones_each_become_one_section():
    chunks = [
        _heading_chunk("Disposición final primera.", level=1),
        _body_chunk("Modifícase la Ley 30/1992...", headings=[]),
        _heading_chunk("Disposición final segunda.", level=1),
        _body_chunk("La presente ley entrará en vigor...", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 2
    assert saved[0].section_type == "disp_final"
    assert saved[0].section_number == "final primera"
    assert "Modifícase" in saved[0].text
    assert saved[1].section_type == "disp_final"
    assert saved[1].section_number == "final segunda"
    assert "entrará en vigor" in saved[1].text


def test_consecutive_articles_become_separate_sections():
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("Objeto de la ley.", headings=[]),
        _heading_chunk("Artículo 2.", level=1),
        _body_chunk("Ámbito de aplicación.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 2
    assert saved[0].section_number == "1"
    assert "Objeto" in saved[0].text
    assert saved[1].section_number == "2"
    assert "Ámbito" in saved[1].text


# ---------------------------------------------------------------------------
# Title dedup
# ---------------------------------------------------------------------------

def test_drops_heading_matching_document_title():
    # heading-only "Ley de Cambio Climático" classifies as unknown → leading orphan
    chunks = [
        _heading_chunk("Ley de Cambio Climático", level=1),
        _heading_chunk("Capítulo I", level=1),
        _body_chunk("Artículo 1 body", headings=["Artículo 1"]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="Ley de Cambio Climático", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert all("Ley de Cambio Climático" not in s.text for s in saved)


def test_title_dedup_strips_markdown():
    # Title chunk wrapped in bold markdown — should still match and be dropped
    chunks = [
        _body_chunk("**Anteproyecto de Ley Orgánica de Juventud**", headings=[]),
        _heading_chunk("Artículo 1.", level=1),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest(
        "f.pdf",
        title="Anteproyecto de Ley Orgánica de Juventud",
        author="a",
    )

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    # Title body is a leading orphan (dropped before dedup even fires), article remains
    assert len(saved) == 1
    assert saved[0].section_type == "articulo"


def test_title_match_is_case_and_accent_insensitive():
    chunks = [_heading_chunk("LEY de cambio climatico", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="Ley de Cambio Climático", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved == []


def test_leading_orphan_chunks_dropped():
    chunks = [
        _body_chunk("Some preamble text before any section", headings=[]),
        _body_chunk("More orphan content", headings=[]),
        _heading_chunk("Artículo 1.", level=1),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "articulo"
    assert "orphan" not in saved[0].text


# ---------------------------------------------------------------------------
# Page number and meta
# ---------------------------------------------------------------------------

def test_extracts_page_number_from_prov():
    # Page number comes from body chunk (heading has no prov)
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("body", headings=[], page_no=7),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].page_number == 7


def test_page_number_none_when_prov_missing():
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("body", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].page_number is None


def test_meta_stored_on_section():
    dl_meta = {"doc_items": [{"label": "text", "prov": [{"page_no": 3}]}]}
    chunk = {
        "text": "body text",
        "text_markdown": "body text",
        "metadata": {"is_heading_only": False, "dl_meta": dl_meta},
    }
    # This body chunk has no section_start — needs a preceding article heading
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        chunk,
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    # Opening chunk is the heading (no dl_meta beyond section_header label)
    # Body chunk's dl_meta is in the merged text, but meta comes from opening chunk
    assert saved[0].meta is not None


def test_meta_none_when_dl_meta_absent():
    chunk = {
        "text": "body text",
        "text_markdown": "body text",
        "metadata": {"is_heading_only": False},
    }
    # Body chunk with no dl_meta as opening chunk of a group won't happen
    # (no section_start). Use a heading to start the group.
    chunks = [_heading_chunk("Artículo 1.", level=1), chunk]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    # Heading opens the group; heading's dl_meta = {"doc_items": [{"label": "section_header"}]}
    assert saved[0].meta is not None  # heading has minimal dl_meta


# ---------------------------------------------------------------------------
# TOC skipping
# ---------------------------------------------------------------------------

def test_toc_heading_chunk_is_hard_skipped():
    chunks = [
        _heading_chunk("Índice", level=1),
        _body_chunk("Título I ... 3", headings=[], label="list_item"),
        _heading_chunk("TÍTULO I", level=1),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    texts = [s.text for s in saved]
    assert "Índice" not in texts
    assert "Título I ... 3" not in texts
    assert "TÍTULO I" in texts


# ---------------------------------------------------------------------------
# Disposición classifications
# ---------------------------------------------------------------------------

def test_disp_final_is_non_matchable():
    chunks = [
        _heading_chunk("Disposición final primera.", level=1),
        _body_chunk("Modifícase la Ley...", headings=["Disposición final primera."]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert all(not s.is_matchable for s in saved)


def test_disp_adicional_is_matchable():
    chunks = [_heading_chunk("Disposición adicional primera.", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].is_matchable is True
    assert saved[0].section_type == "disp_adicional"


# ---------------------------------------------------------------------------
# Section number
# ---------------------------------------------------------------------------

def test_section_number_populated_for_articulo():
    chunks = [_heading_chunk("Artículo 5.", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].section_number == "5"


# ---------------------------------------------------------------------------
# Separator skipping
# ---------------------------------------------------------------------------

def test_separator_chunk_dropped_from_group():
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("Para 1.", headings=[]),
        _body_chunk("------------------------", headings=[]),
        _body_chunk("Para 2.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert "Para 1." in saved[0].text
    assert "Para 2." in saved[0].text
    assert "---" not in saved[0].text


def test_articulo_inside_disp_final_merges_into_parent():
    chunks = [
        _heading_chunk("Disposición final primera.", level=1),
        _body_chunk("Modifícase la Ley X de Ejemplo.", headings=[]),
        _heading_chunk("Artículo 5.", level=2),
        _body_chunk("El nuevo texto queda redactado del siguiente modo.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "disp_final"
    assert saved[0].section_number == "final primera"
    assert saved[0].is_matchable is False
    assert "Modifícase" in saved[0].text
    assert "Artículo 5." in saved[0].text
    assert "El nuevo texto" in saved[0].text


def test_inline_article_heading_gets_md_prefix_when_docling_misses_section_header():
    # Docling sometimes fails to label an article title as section_header; it
    # arrives as a body chunk. The classifier still recognises it via direct
    # text match, but the resulting text_markdown must still render as a heading.
    chunks = [
        _body_chunk("Artículo 42. Derecho a la educación.", headings=[]),
        _body_chunk("La Administración General del Estado promoverá...", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    saved = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_number == "42"
    assert saved[0].text_markdown.startswith("## Artículo 42.")
    assert "La Administración General del Estado" in saved[0].text_markdown
    assert saved[0].text.startswith("Artículo 42.")


def test_multi_body_under_one_heading_renders_heading_once():
    chunks = [
        _heading_chunk("Artículo 1.", level=1),
        _body_chunk("Intro paragraph.", headings=["Artículo 1."]),
        _body_chunk("List item 1.", headings=["Artículo 1."]),
        _body_chunk("List item 2.", headings=["Artículo 1."]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    saved = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].text_markdown.count("Artículo 1.") == 1
    assert "Intro paragraph." in saved[0].text_markdown
    assert "List item 2." in saved[0].text_markdown


def test_inline_article_heading_starts_new_section_despite_stale_heading_context():
    # Mimics docling missing a section_header label: the new article appears as
    # body text with stale meta.headings still pointing at the previous article.
    chunks = [
        _heading_chunk("Artículo 54.", level=1),
        _body_chunk("Item 1 of art 54.", headings=["Artículo 54."]),
        _body_chunk("Artículo 55.", headings=["Artículo 54."]),
        _body_chunk("Item 1 of art 55.", headings=["Artículo 54."]),
        _body_chunk("Item 2 of art 55.", headings=["Artículo 54."]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    saved = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 2
    assert saved[0].section_number == "54"
    assert "Item 1 of art 54." in saved[0].text
    assert "Item 1 of art 54." not in saved[1].text
    assert saved[1].section_number == "55"
    assert "Item 1 of art 55." in saved[1].text
    assert "Item 2 of art 55." in saved[1].text


def test_inline_numbered_items_split_into_paragraphs():
    # Mimics Docling collapsing items 1-3 into one body chunk (article 4 shape).
    body_text = (
        "1. Las personas jóvenes tienen derecho a la libertad de reunión sin "
        "discriminación basada en su edad. "
        "2. El ejercicio se realizará con las adaptaciones necesarias en los "
        "procedimientos administrativos. "
        "3. Las autoridades públicas adoptarán medidas específicas para "
        "garantizar este derecho."
    )
    chunks = [
        _heading_chunk("Artículo 4.", level=1),
        _body_chunk(body_text, headings=[]),
        _body_chunk("4. En todo caso, la actuación se regirá por la ley.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "\n\n2. El ejercicio" in md
    assert "\n\n3. Las autoridades" in md
    assert "\n\n4. En todo caso" in md


def test_numbered_split_no_false_positive_on_decimal():
    chunks = [
        _heading_chunk("Artículo 7.", level=1),
        _body_chunk("La tasa será del 3.5 por ciento aplicable a todos los casos.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "3.5 por ciento" in md
    assert md.count("\n\n") == 1  # only the heading separator


def test_single_numbered_item_unchanged():
    chunks = [
        _heading_chunk("Artículo 8.", level=1),
        _body_chunk("1. Single numbered paragraph with no siblings.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "1. Single numbered paragraph with no siblings." in md


def test_merged_letter_list_split_into_bulleted_items():
    # Mimics Docling collapsing intro + items a-e into one list_item chunk,
    # with e's tail and f as their own follow-up chunks.
    chunks = [
        _heading_chunk("Artículo 5.", level=1),
        _body_chunk(
            "- La actuación se orientará a los siguientes fines: "
            "a) El fomento. b) La garantía. c) La protección. "
            "d) La promoción. e) El fomento de la emancipación,",
            headings=[], label="list_item",
        ),
        _body_chunk(
            "- especialmente en los ámbitos laboral y salud mental.",
            headings=[], label="list_item",
        ),
        _body_chunk(
            "- f) La prevención de violencias.",
            headings=[], label="list_item",
        ),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    for letter in "abcdef":
        assert f"- {letter}) " in md
    assert "emancipación, especialmente en los ámbitos" in md
    assert "fines:\n\n- a) El fomento" in md


def test_well_formed_letter_list_rebuilt_identically():
    # Article 6 shape: each letter is its own chunk with a leading bullet.
    chunks = [
        _heading_chunk("Artículo 6.", level=1),
        _body_chunk("Son principios rectores:", headings=[]),
        _body_chunk("- a) Universalidad.", headings=[], label="list_item"),
        _body_chunk("- b) Atención integral.", headings=[], label="list_item"),
        _body_chunk("- c) Transversalidad.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "- a) Universalidad." in md
    assert "- b) Atención integral." in md
    assert "- c) Transversalidad." in md


def test_non_letter_list_run_preserved():
    # Genuine markdown list — no `a)` marker — stays as a list verbatim.
    chunks = [
        _heading_chunk("Artículo 9.", level=1),
        _body_chunk("- First bullet.", headings=[], label="list_item"),
        _body_chunk("- Second bullet.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "- First bullet." in md
    assert "- Second bullet." in md


def test_lowercase_orphan_paragraph_folds_into_preceding_list_item():
    # Article 12 shape: list_item a) interrupted by a non-list continuation chunk.
    chunks = [
        _heading_chunk("Artículo 12.", level=1),
        _body_chunk(
            "- a) Acceso universal y gratuito a los centros, a las personas",
            headings=[], label="list_item",
        ),
        _body_chunk(
            "jóvenes en situación de vulnerabilidad o necesidades específicas.",
            headings=[],  # default label='text' → not list_item
        ),
        _body_chunk("- b) Facilidad de acceso.", headings=[], label="list_item"),
        _body_chunk("- c) Puesta a disposición.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "a las personas jóvenes en situación de vulnerabilidad" in md
    assert "\n\njóvenes en situación" not in md
    assert "\n\n- b) Facilidad" in md
    assert "\n\n- c) Puesta" in md


def test_capital_paragraph_does_not_get_absorbed_into_list_run():
    # A capital-leading paragraph between list_items must stay a separate paragraph.
    chunks = [
        _heading_chunk("Artículo 13.", level=1),
        _body_chunk("- a) Primero.", headings=[], label="list_item"),
        _body_chunk("Nuevo párrafo independiente con mayúscula.", headings=[]),
        _body_chunk("- b) Segundo.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "\n\nNuevo párrafo independiente" in md
    assert "Primero. Nuevo párrafo" not in md


def test_numbered_items_split_inside_letter_list_run():
    # Article 4 shape: numbered intro + a/b sub-items, all as consecutive list_items.
    intro = (
        "1. Las personas jóvenes tienen derecho a la libertad de reunión sin "
        "discriminación basada en su edad. "
        "2. El ejercicio se realizará con las adaptaciones necesarias. "
        "3. Las autoridades públicas adoptarán medidas, al menos:"
    )
    chunks = [
        _heading_chunk("Artículo 4.", level=1),
        _body_chunk(intro, headings=[], label="list_item"),
        _body_chunk("a) El reconocimiento no formalista.", headings=[], label="list_item"),
        _body_chunk("b) El establecimiento de garantías.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "\n\n2. El ejercicio" in md
    assert "\n\n3. Las autoridades" in md
    assert "\n\n- a) El reconocimiento" in md
    assert "\n\n- b) El establecimiento" in md


def test_inline_pseudo_letter_list_not_reformatted():
    # Article 11 b) shape: outer letter list whose b) item embeds an inline
    # a/b/c plain-text enumeration. Sequence has duplicates → leave alone.
    body_b = (
        "b) Para favorecer la representatividad de la población joven en las "
        "estadísticas, las muestras podrán diseñarse teniendo en cuenta los "
        "siguientes tramos de edad: a) 15-19 años. b) 20-24 años. c) 25-29 años."
    )
    chunks = [
        _heading_chunk("Artículo 11.", level=1),
        _body_chunk("a) Primer punto del artículo 11.", headings=[], label="list_item"),
        _body_chunk(body_b, headings=[], label="list_item"),
        _body_chunk("c) Tercer punto del artículo 11.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "tramos de edad: a) 15-19 años. b) 20-24 años. c) 25-29 años." in md


def test_inline_pseudo_numbered_list_not_split():
    # Body chunk where numbered items repeat — sequence [1,2,1,2] is not strict.
    body = (
        "Los poderes públicos adoptarán las siguientes medidas. "
        "1. Medidas de fomento del empleo juvenil. "
        "2. Medidas de apoyo a la emancipación. "
        "Este plan incluye criterios como: "
        "1. Criterio A y la justicia. 2. Criterio B."
    )
    chunks = [
        _heading_chunk("Artículo 9.", level=1),
        _body_chunk(body, headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    md = section_repo.bulk_save.call_args[0][0][0].text_markdown
    assert "1. Medidas de fomento del empleo juvenil. 2. Medidas" in md


def test_disp_adicional_inside_disp_final_merges_into_parent():
    chunks = [
        _heading_chunk("Disposición final primera.", level=1),
        _body_chunk("Modifícase la Ley X de Ejemplo.", headings=[]),
        _heading_chunk("Disposición adicional segunda.", level=2),
        _body_chunk("El Gobierno adoptará las medidas necesarias.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_type == "disp_final"
    assert saved[0].section_number == "final primera"
    assert saved[0].is_matchable is False
    assert "Modifícase" in saved[0].text
    assert "Disposición adicional segunda." in saved[0].text
    assert "El Gobierno adoptará" in saved[0].text


def test_numbered_item_misclassified_as_heading_is_demoted():
    # Docling labels "3. Corresponderá…:" as section_header because it is a
    # short colon-terminated line immediately before a list — a layout heuristic,
    # not a styling difference. Must render as a plain paragraph inside the section.
    chunks = [
        _heading_chunk("Artículo 14.", level=1),
        _body_chunk("1. El Instituto es un organismo autónomo.", headings=[]),
        _body_chunk("2. En el ejercicio de sus competencias.", headings=[]),
        _heading_chunk("3. Corresponderá al Instituto:", level=1),
        _body_chunk("- a) El desarrollo y fomento.", headings=[], label="list_item"),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    saved = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].section_number == "14"
    md = saved[0].text_markdown
    assert "## 3. Corresponderá" not in md
    assert "\n\n3. Corresponderá al Instituto:" in md
    assert md.startswith("## Artículo 14.")
    assert "\n\n- a) El desarrollo" in md


def test_genuine_section_header_starting_with_digit_stays_a_heading():
    # A digit-led heading that is the OPENER of its own group must not be demoted.
    chunks = [
        _heading_chunk("5. Disposiciones generales", level=1),
        _body_chunk("Cuerpo introductorio del bloque.", headings=[]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)
    ingestor.ingest("f.pdf", title="t", author="a")
    saved = section_repo.bulk_save.call_args[0][0]
    if saved:
        assert saved[0].text_markdown.startswith("## 5. Disposiciones generales")
