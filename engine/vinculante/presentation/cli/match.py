import typer

from vinculante.application.matching.matcher_service import MatcherService
from vinculante.application.summary.summary_service import SummaryService
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.embeddings.factory import create_embedder_from_env
from vinculante.infrastructure.llm.factory import create_llm_from_env, create_summary_llm_from_env

app = typer.Typer(help="Run the matching pipeline.")


@app.command("run")
def run_matching(
    target_id: int = typer.Option(..., help="Target document to match proposals against"),
    topic: str | None = typer.Option(
        None, "--topic", help="Only match proposals whose topic matches (case-insensitive exact)"
    ),
    skip_matched: bool = typer.Option(False, help="Skip proposals that already have matches"),
    skip_summary: bool | None = typer.Option(
        None, "--skip-summary/--no-skip-summary",
        help="Skip executive summary generation after matching (default: True when --topic is set)",
    ),
):
    """Match all proposals to sections using vector similarity + LLM."""
    skip = skip_summary if skip_summary is not None else bool(topic)
    settings = get_settings()
    embedder = create_embedder_from_env(settings)
    llm = create_llm_from_env(settings)
    with SessionLocal() as db:
        match_service = MatcherService(
            proposal_repo=ProposalRepository(db),
            section_repo=SectionRepository(db),
            match_repo=MatchRepository(db),
            target_repo=TargetRepository(db),
            embedder=embedder,
            llm=llm,
            settings=settings,
        )
        matches = match_service.run(target_id=target_id, topic=topic, skip_matched=skip_matched)
        typer.echo(f"Created {len(matches)} matches")

        if not skip:
            typer.echo("Generating executive summary…")
            summary_llm = create_summary_llm_from_env(settings)
            summary_service = SummaryService(
                section_repo=SectionRepository(db),
                match_repo=MatchRepository(db),
                proposal_repo=ProposalRepository(db),
                target_repo=TargetRepository(db),
                llm=summary_llm,
                settings=settings,
            )
            summary_service.run(target_id=target_id)
            typer.echo("Executive summary saved.")
