from pathlib import Path

from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.loaders.csv_loader import CsvLoader

FIXTURES = Path(__file__).parents[3] / "fixtures"


def test_ingests_csv_rows_and_maps_all_fields(db_session):
    repo = ProposalRepository(db_session)
    ingestor = ProposalIngestor(repo=repo, loader=CsvLoader())
    file_path = str(FIXTURES / "proposals_basic.csv")

    ingestor.ingest(file_path)

    proposals = {p.reference: p for p in repo.get_all()}
    assert len(proposals) == 3
    p = proposals["ref-1"]
    assert p.text == "Regular la IA"
    assert p.author == "Alice"
    assert p.author_type == "ciudadania"
    assert p.topic == "digital"
    assert p.subtopic == "ia"
    assert p.source_file == file_path


def test_skips_rows_with_empty_text(db_session):
    repo = ProposalRepository(db_session)
    ingestor = ProposalIngestor(repo=repo, loader=CsvLoader())

    ingestor.ingest(str(FIXTURES / "proposals_with_empty.csv"))

    texts = sorted(p.text for p in repo.get_all())
    assert texts == ["Tres", "Uno"]
