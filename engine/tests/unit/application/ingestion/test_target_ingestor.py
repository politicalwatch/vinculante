from unittest.mock import MagicMock

from vinculante.application.ingestion.target_ingestor import TargetIngestor
from vinculante.domain.entities import Section, TargetDocument


def _body_chunk(text: str, headings: list[str], label: str = "list_item", page_no: int | None = None) -> dict:
    doc_item: dict = {"label": label}
    if page_no is not None:
        doc_item["prov"] = [{"page_no": page_no}]
    return {
        "text": text,
        "text_markdown": text,
        "metadata": {
            "is_heading_only": False,
            "headings": headings,
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


def test_heading_only_chunk_becomes_non_matchable_section_header():
    chunks = [_heading_chunk("Capítulo I", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].text == "Capítulo I"
    assert saved[0].section_type == "section_header"
    assert saved[0].is_matchable is False
    assert saved[0].text_markdown == "## Capítulo I"


def test_body_chunk_becomes_matchable_section():
    chunks = [_body_chunk("body text", headings=["Artículo 1"], label="list_item")]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].text == "body text"
    assert saved[0].section_type == "list_item"
    assert saved[0].is_matchable is True


def test_drops_heading_matching_document_title():
    chunks = [
        _heading_chunk("Ley de Cambio Climático", level=1),
        _heading_chunk("Capítulo I", level=1),
        _body_chunk("body", headings=["Artículo 1"]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="Ley de Cambio Climático", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert [s.text for s in saved] == ["Capítulo I", "body"]


def test_title_match_is_case_and_accent_insensitive():
    chunks = [_heading_chunk("LEY de cambio climatico", level=1)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="Ley de Cambio Climático", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved == []


def test_extracts_page_number_from_prov():
    chunks = [_body_chunk("body", headings=[], page_no=7)]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].page_number == 7


def test_page_number_none_when_prov_missing():
    chunks = [_body_chunk("body", headings=[])]  # no page_no kwarg → no prov
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
    ingestor, section_repo = _make_ingestor([chunk])

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].meta == dl_meta


def test_meta_none_when_dl_meta_absent():
    chunk = {
        "text": "body text",
        "text_markdown": "body text",
        "metadata": {"is_heading_only": False},
    }
    ingestor, section_repo = _make_ingestor([chunk])

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert saved[0].meta is None


def test_preserves_chunk_order():
    chunks = [
        _heading_chunk("Capítulo I", level=1),
        _body_chunk("Artículo 1 body", headings=["Artículo 1"]),
        _heading_chunk("Capítulo II", level=1),
        _body_chunk("Artículo 2 body", headings=["Artículo 2"]),
    ]
    ingestor, section_repo = _make_ingestor(chunks)

    ingestor.ingest("f.pdf", title="t", author="a")

    saved: list[Section] = section_repo.bulk_save.call_args[0][0]
    assert [s.text for s in saved] == [
        "Capítulo I",
        "Artículo 1 body",
        "Capítulo II",
        "Artículo 2 body",
    ]
    assert [s.is_matchable for s in saved] == [False, True, False, True]
