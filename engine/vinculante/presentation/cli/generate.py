import typer

from vinculante.application.clear_language.generator_service import ClearLanguageGeneratorService
from vinculante.application.summary.summary_service import SummaryService
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.llm.factory import create_llm_from_env, create_summary_llm_from_env

app = typer.Typer(help="Run one-off generation steps (clear-language, summary, ...).")


@app.command("clear-language")
def generate_clear_language(
    target_id: int = typer.Option(None, help="Regenerate only sections of this target"),
    force: bool = typer.Option(
        False, help="Regenerate even if clear_language already differs from text"
    ),
):
    """Generate clear-language rewrite for target sections via LLM."""
    settings = get_settings()
    llm = create_llm_from_env(settings)
    with SessionLocal() as db:
        section_repo = SectionRepository(db)
        service = ClearLanguageGeneratorService(section_repo=section_repo, llm=llm)
        count = service.generate(target_id=target_id, force=force)
    typer.echo(f"Regenerated clear_language for {count} sections")


@app.command("summary")
def generate_summary(
    target_id: int = typer.Argument(..., help="Target document to generate summary for"),
):
    """Generate (or regenerate) the executive summary for a target document."""
    settings = get_settings()
    llm = create_summary_llm_from_env(settings)
    with SessionLocal() as db:
        service = SummaryService(
            section_repo=SectionRepository(db),
            match_repo=MatchRepository(db),
            proposal_repo=ProposalRepository(db),
            target_repo=TargetRepository(db),
            llm=llm,
            settings=settings,
        )
        summary = service.run(target_id=target_id)
    typer.echo(f"Executive summary saved ({len(summary)} chars).")
