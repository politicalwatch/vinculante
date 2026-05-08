from pathlib import Path

from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor
from vinculante.domain.entities import TargetDocument
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
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
    assert p.author_type == "citizen"
    assert p.topic == "digital"
    assert p.subtopic == "ia"
    assert p.source_file == file_path


def test_skips_rows_with_empty_text(db_session):
    repo = ProposalRepository(db_session)
    ingestor = ProposalIngestor(repo=repo, loader=CsvLoader())

    ingestor.ingest(str(FIXTURES / "proposals_with_empty.csv"))

    texts = sorted(p.text for p in repo.get_all())
    assert texts == ["Tres", "Uno"]


def test_stamps_target_id_on_ingested_proposals(db_session):
    target = TargetRepository(db_session).save(TargetDocument(title="t", author="a"))
    repo = ProposalRepository(db_session)
    ingestor = ProposalIngestor(repo=repo, loader=CsvLoader())

    ingestor.ingest(str(FIXTURES / "proposals_basic.csv"), target_id=target.id)

    assert all(p.target_id == target.id for p in repo.get_all())


def test_target_id_is_none_when_not_provided(db_session):
    repo = ProposalRepository(db_session)
    ingestor = ProposalIngestor(repo=repo, loader=CsvLoader())

    ingestor.ingest(str(FIXTURES / "proposals_basic.csv"))

    assert all(p.target_id is None for p in repo.get_all())
