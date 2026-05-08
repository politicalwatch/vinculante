from pathlib import Path

import pytest

from vinculante.application.ingestion.target_ingestor import TargetIngestor
from vinculante.infrastructure.chunking.docling_chunker import DoclingChunker
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository

FIXTURE_PDF = Path(__file__).parents[3] / "fixtures" / "sample_target.pdf"


@pytest.fixture(scope="module")
def chunker() -> DoclingChunker:
    return DoclingChunker()


def test_ingests_target_document_with_metadata_and_sections(db_session, chunker):
    target_repo = TargetRepository(db_session)
    section_repo = SectionRepository(db_session)
    ingestor = TargetIngestor(target_repo=target_repo, section_repo=section_repo, chunker=chunker)

    target = ingestor.ingest(
        file_path=str(FIXTURE_PDF),
        title="Ley de ejemplo",
        author="Congreso",
        version="v1",
    )

    assert target.id is not None
    assert target.title == "Ley de ejemplo"
    assert target.author == "Congreso"
    assert target.version == "v1"

    sections = section_repo.get_by_target(target.id)
    assert len(sections) >= 1
    assert all(s.target_id == target.id for s in sections)
    all_text = " ".join(s.text for s in sections)
    assert "Artículo 1" in all_text
    assert "Transparencia" in all_text

    heading_sections = [s for s in sections if not s.is_matchable]
    body_sections = [s for s in sections if s.is_matchable]
    assert len(heading_sections) >= 1
    assert all(s.section_type == "section_header" for s in heading_sections)
    assert all(s.clear_language == s.text for s in heading_sections)
    assert all(s.is_matchable for s in body_sections)
    heading_texts = " ".join(s.text for s in heading_sections)
    assert "Capítulo" in heading_texts

    assert any(s.page_number is not None for s in sections)
    assert any(s.meta is not None and "doc_items" in s.meta for s in sections)
