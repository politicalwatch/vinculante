import typer

from vinculante.presentation.cli import db, embed, export, generate, ingest, match

app = typer.Typer(name="vinculante", help="Vinculante CLI — ingest, embed, match, export.")

app.add_typer(ingest.app, name="ingest")
app.add_typer(embed.app, name="embed")
app.add_typer(generate.app, name="generate")
app.add_typer(match.app, name="match")
app.add_typer(export.app, name="export")
app.add_typer(db.app, name="db")
