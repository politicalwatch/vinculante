import csv
from pathlib import Path
from typing import Optional

import typer

from vinculante.application.clear_language.generator_service import ClearLanguageGeneratorService
from vinculante.application.ingestion.proposal_ingestor import ProposalIngestor
from vinculante.application.ingestion.target_ingestor import TargetIngestor
from vinculante.infrastructure.chunking.docling_chunker import DoclingChunker
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.llm.factory import create_llm_from_env, create_report_llm_from_env
from vinculante.infrastructure.loaders.csv_loader import CsvLoader
from vinculante.infrastructure.loaders.docx_loader import DocxLoader
from vinculante.infrastructure.loaders.xlsx_loader import XlsxLoader

app = typer.Typer(help="Ingest proposals and target documents.")


class _PreviewDumpingLoader:
    """Wraps any loader and writes its output to a sidecar CSV for inspection."""

    def __init__(self, inner, csv_path: Path) -> None:
        self._inner = inner
        self._csv_path = csv_path

    def load(self, file_path: str) -> list[dict]:
        rows = self._inner.load(file_path)
        if rows:
            with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            typer.echo(f"Preview CSV written to {self._csv_path}")
        return rows


def _loader_for(path: Path, use_report_loader: bool):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return CsvLoader()
    if suffix in (".xlsx", ".xls"):
        return XlsxLoader()
    if use_report_loader:
        if suffix in (".docx", ".pdf"):
            from vinculante.infrastructure.loaders.report_loader import ReportLoader
            settings = get_settings()
            llm = create_report_llm_from_env(settings)
            return ReportLoader(llm=llm, settings=settings)
        raise typer.BadParameter(
            f"--use-report-loader only supports .docx and .pdf (got {suffix})"
        )
    if suffix == ".docx":
        return DocxLoader()
    if suffix == ".pdf":
        raise typer.BadParameter("PDF proposals require --use-report-loader")
    raise typer.BadParameter(f"Unsupported proposals file extension: {suffix}")


@app.command("proposals")
def ingest_proposals(
    file: Path = typer.Option(..., help="Path to csv/xlsx/docx/pdf with proposals"),
    target_id: Optional[int] = typer.Option(None, help="Link ingested proposals to this target document"),
    author_type: Optional[str] = typer.Option(
        None,
        help="Default author_type for rows missing it in the file",
    ),
    use_report_loader: bool = typer.Option(
        False,
        "--use-report-loader",
        help="Parse the input as a long-form report (PDF/DOCX) with the "
             "LLM-assisted ReportLoader. Required for PDF input.",
    ),
    preview_csv: bool = typer.Option(
        False, help="Write a sidecar .preview.csv next to the input file"
    ),
):
    """Load proposals from a file into the database."""
    loader = _loader_for(file, use_report_loader)
    if preview_csv:
        if file.suffix.lower() not in (".docx", ".pdf"):
            raise typer.BadParameter("--preview-csv is only supported for .docx and .pdf input")
        loader = _PreviewDumpingLoader(loader, file.with_suffix(".preview.csv"))
    with SessionLocal() as db:
        repo = ProposalRepository(db)
        ingestor = ProposalIngestor(repo=repo, loader=loader)
        proposals = ingestor.ingest(str(file), target_id=target_id, author_type=author_type)
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
