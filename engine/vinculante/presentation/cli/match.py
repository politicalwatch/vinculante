import typer

from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.embeddings.factory import create_embedder_from_env
from vinculante.infrastructure.llm.factory import create_llm_from_env
from vinculante.application.matching.matcher_service import MatcherService

app = typer.Typer(help="Run the matching pipeline.")


@app.command("run")
def run_matching(
    target_id: int = typer.Option(..., help="Target document to match proposals against"),
    skip_matched: bool = typer.Option(False, help="Skip proposals that already have matches"),
):
    """Match all proposals to sections using vector similarity + LLM."""
    settings = get_settings()
    embedder = create_embedder_from_env(settings)
    llm = create_llm_from_env(settings)
    with SessionLocal() as db:
        service = MatcherService(
            proposal_repo=ProposalRepository(db),
            section_repo=SectionRepository(db),
            match_repo=MatchRepository(db),
            target_repo=TargetRepository(db),
            embedder=embedder,
            llm=llm,
            settings=settings,
        )
        matches = service.run(target_id=target_id, skip_matched=skip_matched)
    typer.echo(f"Created {len(matches)} matches")
