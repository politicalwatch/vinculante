import typer

from vinculante.application.embedding.embedder_service import (
    ProposalEmbedderService,
    SectionEmbedderService,
)
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.embeddings.factory import create_embedder_from_env

app = typer.Typer(help="Compute and store embeddings.")


@app.command("sections")
def embed_sections(
    target_id: int = typer.Option(None, help="Embed only sections of this target document"),
):
    """Embed all unembedded sections and store vectors in the database."""
    settings = get_settings()
    embedder = create_embedder_from_env(settings)
    with SessionLocal() as db:
        section_repo = SectionRepository(db)
        service = SectionEmbedderService(section_repo=section_repo, embedder=embedder)
        count = service.embed_sections(target_id=target_id)
    typer.echo(f"Embedded {count} sections")


@app.command("proposals")
def embed_proposals(
    source_file: str = typer.Option(None, help="Embed only proposals from this source file"),
):
    """Embed all unembedded proposals and store vectors in the database."""
    settings = get_settings()
    embedder = create_embedder_from_env(settings)
    with SessionLocal() as db:
        proposal_repo = ProposalRepository(db)
        service = ProposalEmbedderService(proposal_repo=proposal_repo, embedder=embedder)
        count = service.embed_proposals(source_file=source_file)
    typer.echo(f"Embedded {count} proposals")
