import typer

from vinculante.application.plain_text.generator_service import PlainTextGeneratorService
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.llm.factory import create_llm_from_env

app = typer.Typer(help="Run one-off generation steps (plain-text, ...).")


@app.command("plain-text")
def generate_plain_text(
    target_id: int = typer.Option(None, help="Regenerate only sections of this target"),
    force: bool = typer.Option(False, help="Regenerate even if plain_text already differs from text"),
):
    """Generate clear-language plain_text for target sections via LLM."""
    settings = get_settings()
    llm = create_llm_from_env(settings)
    with SessionLocal() as db:
        section_repo = SectionRepository(db)
        service = PlainTextGeneratorService(section_repo=section_repo, llm=llm)
        count = service.generate(target_id=target_id, force=force)
    typer.echo(f"Regenerated plain_text for {count} sections")
