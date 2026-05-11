from pathlib import Path

import typer

from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor
from vinculante.application.ingestion.target_ingestor import TargetIngestor
from vinculante.application.clear_language.generator_service import ClearLanguageGeneratorService
from vinculante.infrastructure.chunking.docling_chunker import DoclingChunker
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.llm.factory import create_llm_from_env
from vinculante.infrastructure.loaders.csv_loader import CsvLoader
from vinculante.infrastructure.loaders.xlsx_loader import XlsxLoader

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
    target_id: int = typer.Option(None, help="Link ingested proposals to this target document"),
):
    """Load proposals from a file into the database."""
    with SessionLocal() as db:
        repo = ProposalRepository(db)
        loader = _loader_for(file)
        ingestor = ProposalIngestor(repo=repo, loader=loader)
        proposals = ingestor.ingest(str(file), target_id=target_id)
    typer.echo(f"Ingested {len(proposals)} proposals from {file}")


@app.command("target")
def ingest_target(
    file: Path = typer.Option(..., help="Path to .docx or .pdf to ingest as target document"),
    title: str = typer.Option(..., help="Document title"),
    author: str = typer.Option(..., help="Document author"),
    version: str = typer.Option(None, help="Document version"),
):
    """Chunk and load a target normative document into the database."""
    settings = get_settings()
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
        typer.echo(f"Ingested target document '{target.title}' (id={target.id})")

        llm = create_llm_from_env(settings)
        generator = ClearLanguageGeneratorService(section_repo=section_repo, llm=llm)
        count = generator.generate(target_id=target.id)
    typer.echo(f"Generated clear_language for {count} sections")
