import typer

from vinculante.application.clear_language.generator_service import ClearLanguageGeneratorService
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.llm.factory import create_llm_from_env

app = typer.Typer(help="Run one-off generation steps (clear-language, ...).")


@app.command("clear-language")
def generate_clear_language(
    target_id: int = typer.Option(None, help="Regenerate only sections of this target"),
    force: bool = typer.Option(False, help="Regenerate even if clear_language already differs from text"),
):
    """Generate clear-language rewrite for target sections via LLM."""
    settings = get_settings()
    llm = create_llm_from_env(settings)
    with SessionLocal() as db:
        section_repo = SectionRepository(db)
        service = ClearLanguageGeneratorService(section_repo=section_repo, llm=llm)
        count = service.generate(target_id=target_id, force=force)
    typer.echo(f"Regenerated clear_language for {count} sections")
