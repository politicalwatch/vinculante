from pathlib import Path

import typer

from vinculante.infrastructure.chunking.docling_chunker import DoclingChunker
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.loaders.csv_loader import CsvLoader
from vinculante.infrastructure.loaders.xlsx_loader import XlsxLoader
from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor
from vinculante.application.ingestion.target_ingestor import TargetIngestor

app = typer.Typer(help="Ingest proposals and target documents.")


def _loader_for(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return CsvLoader()
    if suffix in (".xlsx", ".xls"):
        return XlsxLoader()
    raise typer.BadParameter(f"Unsupported proposals file extension: {suffix}")


@app.command("proposals")
def ingest_proposals(
    file: Path = typer.Option(..., help="Path to csv/xlsx with proposals (must contain a 'text' column)"),
):
    """Load proposals from a file into the database."""
    with SessionLocal() as db:
        repo = ProposalRepository(db)
        loader = _loader_for(file)
        ingestor = ProposalIngestor(repo=repo, loader=loader)
        proposals = ingestor.ingest(str(file))
    typer.echo(f"Ingested {len(proposals)} proposals from {file}")


@app.command("target")
def ingest_target(
    file: Path = typer.Option(..., help="Path to docx to ingest as target document"),
    title: str = typer.Option(..., help="Document title"),
    author: str = typer.Option(..., help="Document author"),
    version: str = typer.Option(None, help="Document version"),
):
    """Chunk and load a target normative document into the database."""
    with SessionLocal() as db:
        target_repo = TargetRepository(db)
        section_repo = SectionRepository(db)
        chunker = DoclingChunker()
        ingestor = TargetIngestor(
            target_repo=target_repo,
            section_repo=section_repo,
            chunker=chunker,
        )
        target = ingestor.ingest(str(file), title=title, author=author, version=version)
        msg = f"Ingested target document '{target.title}' (id={target.id})"
    typer.echo(msg)
