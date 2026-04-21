import typer

app = typer.Typer(help="Database utilities.")


@app.command("reset")
def reset_db(
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
):
    """Drop and recreate all tables (destructive)."""
    if not confirm:
        typer.confirm("This will drop all data. Continue?", abort=True)
    from vinculante.domain.base import Base
    import vinculante.domain.entities  # noqa: F401 — register all models
    from vinculante.infrastructure.db.session import _engine
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    typer.echo("Database reset complete.")
