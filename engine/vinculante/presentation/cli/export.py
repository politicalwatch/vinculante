from pathlib import Path

import typer

from vinculante.domain.entities import MatchStatus
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.application.export.match_exporter import MatchExporter

app = typer.Typer(help="Export data.")


@app.command("matches")
def export_matches(
    output: Path = typer.Option(None, help="Output file path (default: data/export/matches[_target_<id>].<format>)"),
    match_status: str = typer.Option(None, help="Filter by status: pending|confirmed|rejected"),
    include_rejected: bool = typer.Option(
        False,
        help="Include matches with degree='ninguno' (LLM-rejected). Useful for debugging.",
    ),
    target_id: int = typer.Option(None, "--target-id", help="Filter matches whose proposal belongs to this target document id"),
    fmt: str = typer.Option("csv", "--format", help="Output format: csv|xlsx"),
):
    """Export matches to a CSV or xlsx file."""
    if fmt not in ("csv", "xlsx"):
        typer.echo(f"Invalid format '{fmt}'. Choose csv or xlsx.", err=True)
        raise typer.Exit(1)
    stem = f"matches_target_{target_id}" if target_id is not None else "matches"
    if output is None:
        output = Path(f"data/export/{stem}.{fmt}")
    status = MatchStatus(match_status) if match_status else None
    kwargs = dict(status=status, include_rejected=include_rejected, target_id=target_id)
    with SessionLocal() as db:
        repo = MatchRepository(db)
        exporter = MatchExporter(match_repo=repo)
        if fmt == "xlsx":
            count = exporter.export_to_xlsx(str(output), **kwargs)
        else:
            count = exporter.export_to_csv(str(output), **kwargs)
    typer.echo(f"Exported {count} matches to {output}")
