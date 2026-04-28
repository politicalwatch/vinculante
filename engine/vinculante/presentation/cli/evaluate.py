from pathlib import Path

import typer

from vinculante.application.evaluation.evaluator_service import EvaluatorService
from vinculante.application.evaluation.report_writer import write_report
from vinculante.application.evaluation.retrieval_audit import (
    RetrievalAuditReport,
    run_retrieval_audit,
    write_retrieval_report,
)
from vinculante.application.evaluation.testset import load_testset
from vinculante.infrastructure.config.settings import get_settings
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository
from vinculante.infrastructure.db.repositories.targets import TargetRepository
from vinculante.infrastructure.db.session import SessionLocal
from vinculante.infrastructure.embeddings.factory import create_embedder_from_env

app = typer.Typer(help="Evaluate match results against ground-truth testsets.")

_FMT = "{:<55} {:>6} {:>6} {:>6}  {:>7} {:>7} {:>7}"
_ROW = "{:<55} {:>6} {:>6} {:>6}  {:>7.3f} {:>7.3f} {:>7.3f}"
_AGG = "{:<55} {:>6} {:>6} {:>6}  {:>7.3f} {:>7.3f} {:>7.3f}"


def _print_report(report) -> None:
    typer.echo(f"\n{'='*40} {report.domain.upper()} (target_id={report.target_id}) {'='*40}")
    typer.echo(_FMT.format("Article", "TP", "FP", "FN", "Prec", "Rec", "F1"))
    typer.echo("-" * 100)
    for m in report.article_metrics:
        label = m.article[:54]
        typer.echo(_ROW.format(label, m.tp, m.fp, m.fn, m.precision, m.recall, m.f1))
    typer.echo("-" * 100)
    a = report.aggregate
    typer.echo(_AGG.format("MICRO", "-", "-", "-", a.micro_precision, a.micro_recall, a.micro_f1))
    typer.echo(_AGG.format("MACRO", "-", "-", "-", a.macro_precision, a.macro_recall, a.macro_f1))

    d = report.diagnostics
    if d.unmapped_articles:
        typer.echo(f"\n  [!] Articles with no resolved sections ({len(d.unmapped_articles)}):")
        for a in d.unmapped_articles:
            typer.echo(f"      - {a}")
    if d.unmapped_refs:
        typer.echo(f"\n  [!] Proposal refs with no resolved proposal ({len(d.unmapped_refs)}):")
        for r in d.unmapped_refs:
            typer.echo(f"      - {r}")
    if d.unrelated_matches:
        typer.echo(f"\n  [i] Matches to sections outside expected articles: {d.unrelated_matches}")


@app.command("run")
def run_evaluation(
    testset: Path = typer.Option(
        Path("data/eval/testset.json"),
        help="Path to testset.json",
        exists=True,
    ),
    domain: str = typer.Option(None, help="Evaluate only this domain"),
    out_dir: Path = typer.Option(
        None, help="Directory to write run JSON (default: <testset_dir>/runs)"
    ),
    min_confidence: float = typer.Option(
        None,
        help="Confidence threshold (defaults to matching_confidence_threshold setting)",
    ),
    min_degree: str = typer.Option(
        "bajo",
        help="Min degree to count as positive: alto, medio, bajo (default: bajo)",
    ),
):
    """Score match results against ground-truth pairs in a testset."""
    if min_degree not in ("alto", "medio", "bajo"):
        typer.echo(f"[!] Invalid --min-degree '{min_degree}'. Must be: alto, medio, bajo.")
        raise typer.Exit(1)

    cases = load_testset(testset)
    if domain:
        cases = [c for c in cases if c.domain == domain]
        if not cases:
            typer.echo(f"No cases found for domain '{domain}'.")
            raise typer.Exit(1)

    run_dir = out_dir or testset.parent / "runs"
    settings = get_settings()
    threshold = (
        min_confidence if min_confidence is not None else settings.matching_confidence_threshold
    )

    with SessionLocal() as db:
        service = EvaluatorService(
            section_repo=SectionRepository(db),
            proposal_repo=ProposalRepository(db),
            match_repo=MatchRepository(db),
        )
        target_repo = TargetRepository(db)

        for case in cases:
            target = target_repo.get_by_title_contains(case.domain.upper())
            if target is None:
                typer.echo(f"[!] No target document found for domain '{case.domain}'. Skipping.")
                continue

            report = service.evaluate(
                case, target.id, min_confidence=threshold, min_degree=min_degree
            )
            _print_report(report)

            out_path = write_report(report, testset, settings, run_dir, min_degree=min_degree)
            typer.echo(f"\n  Run saved → {out_path}\n")


_RET_HDR = "{:<55} {:>6} {:>7} {:>7} {:>7} {:>7}"
_RET_ROW = "{:<55} {:>6} {:>7.2f} {:>7.2f} {:>7.2f} {:>7.2f}"


def _print_retrieval_report(report: RetrievalAuditReport) -> None:
    typer.echo(
        f"\n{'='*40} {report.domain.upper()} retrieval"
        f" (target_id={report.target_id}, metric={report.distance_metric}) {'='*40}"
    )
    typer.echo(_RET_HDR.format("Article", "pairs", "@1", "@2", "@3", "@5"))
    typer.echo("-" * 90)
    for m in report.article_metrics:
        r = m.recall_at_k
        typer.echo(_RET_ROW.format(m.article[:54], m.n_pairs, r[1], r[2], r[3], r[5]))
    typer.echo("-" * 90)
    r = report.recall_at_k
    typer.echo(_RET_ROW.format("OVERALL", report.n_pairs, r[1], r[2], r[3], r[5]))
    typer.echo(f"\n  [i] Distance metric: {report.distance_metric} | Pairs: {report.n_pairs}")


@app.command("retrieval")
def run_retrieval_evaluation(
    testset: Path = typer.Option(
        Path("data/eval/testset.json"),
        help="Path to testset.json",
        exists=True,
    ),
    domain: str = typer.Option(None, help="Evaluate only this domain"),
    out_dir: Path = typer.Option(None, help="Output dir (default: <testset_dir>/runs)"),
):
    """Audit retrieval recall@K against ground-truth pairs. Run before tuning top_k."""
    cases = load_testset(testset)
    if domain:
        cases = [c for c in cases if c.domain == domain]
        if not cases:
            typer.echo(f"No cases found for domain '{domain}'.")
            raise typer.Exit(1)

    settings = get_settings()
    embedder = create_embedder_from_env(settings)
    run_dir = out_dir or testset.parent / "runs"

    with SessionLocal() as db:
        target_repo = TargetRepository(db)
        section_repo = SectionRepository(db)
        proposal_repo = ProposalRepository(db)

        for case in cases:
            target = target_repo.get_by_title_contains(case.domain.upper())
            if target is None:
                typer.echo(f"[!] No target found for domain '{case.domain}'. Skipping.")
                continue

            report = run_retrieval_audit(case, target.id, section_repo, proposal_repo, embedder)
            _print_retrieval_report(report)

            out_path = write_retrieval_report(report, run_dir)
            typer.echo(f"\n  Run saved → {out_path}\n")
