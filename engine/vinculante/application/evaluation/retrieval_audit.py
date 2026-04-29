from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from vinculante.application.evaluation.resolver import resolve_articles
from vinculante.application.evaluation.testset import EvalCase
from vinculante.application.matching.top_k import compute_top_k
from vinculante.domain.ports.embeddings import EmbedderProtocol
from vinculante.domain.ports.repositories import (
    ProposalRepositoryProtocol,
    SectionRepositoryProtocol,
)
from vinculante.infrastructure.config.settings import Settings

_KS = [1, 3, 5, 10, 20]
_DISTANCE_METRIC = "l2"


@dataclass
class ArticleRetrievalMetrics:
    article: str
    n_pairs: int
    hits_at_k: dict[int, int]
    recall_at_k: dict[int, float]


@dataclass
class RetrievalAuditReport:
    domain: str
    target_id: int
    n_pairs: int
    n_matchable_sections: int
    effective_top_k: int
    recall_at_k: dict[int, float]
    distance_metric: str
    article_metrics: list[ArticleRetrievalMetrics]


def run_retrieval_audit(
    case: EvalCase,
    target_id: int,
    section_repo: SectionRepositoryProtocol,
    proposal_repo: ProposalRepositoryProtocol,
    embedder: EmbedderProtocol,
    settings: Settings,
) -> RetrievalAuditReport:
    sections = section_repo.get_by_target(target_id)
    n_matchable_sections = sum(1 for s in sections if s.is_matchable)
    effective_top_k = compute_top_k(n_matchable_sections, settings)
    proposals = proposal_repo.get_by_target(target_id)

    article_section_map = resolve_articles(sections, [e.article for e in case.expected])
    ref_to_proposal = {p.reference: p for p in proposals if p.reference}

    total_hits: dict[int, int] = {k: 0 for k in _KS}
    total_pairs = 0
    article_metrics: list[ArticleRetrievalMetrics] = []

    for entry in case.expected:
        expected_ids = set(article_section_map.get(entry.article, []))
        art_hits: dict[int, int] = {k: 0 for k in _KS}
        art_pairs = 0

        for ref in entry.proposal_refs:
            prop = ref_to_proposal.get(ref)
            if prop is None or not prop.text:
                continue
            if prop.embedding is not None:
                embedding = list(prop.embedding)
            else:
                embedding = embedder.embed_query(prop.text)

            retrieved_ids = [
                s.id for s in section_repo.find_similar(embedding, target_id, max(_KS))
            ]
            art_pairs += 1
            for k in _KS:
                if set(retrieved_ids[:k]) & expected_ids:
                    art_hits[k] += 1

        total_pairs += art_pairs
        for k in _KS:
            total_hits[k] += art_hits[k]

        art_recall = {k: art_hits[k] / art_pairs if art_pairs else 0.0 for k in _KS}
        article_metrics.append(
            ArticleRetrievalMetrics(
                article=entry.article,
                n_pairs=art_pairs,
                hits_at_k=art_hits,
                recall_at_k=art_recall,
            )
        )

    overall_recall = {k: total_hits[k] / total_pairs if total_pairs else 0.0 for k in _KS}

    return RetrievalAuditReport(
        domain=case.domain,
        target_id=target_id,
        n_pairs=total_pairs,
        n_matchable_sections=n_matchable_sections,
        effective_top_k=effective_top_k,
        recall_at_k=overall_recall,
        distance_metric=_DISTANCE_METRIC,
        article_metrics=article_metrics,
    )


def write_retrieval_report(report: RetrievalAuditReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=UTC)
    filename = f"retrieval-{now.strftime('%Y%m%d-%H%M%S')}-{report.domain}.json"
    payload = {
        "run_at": now.isoformat(),
        "domain": report.domain,
        "target_id": report.target_id,
        "distance_metric": report.distance_metric,
        "n_pairs": report.n_pairs,
        "n_matchable_sections": report.n_matchable_sections,
        "effective_top_k": report.effective_top_k,
        "recall_at_k": {str(k): v for k, v in report.recall_at_k.items()},
        "article_metrics": [
            {
                "article": m.article,
                "n_pairs": m.n_pairs,
                "hits_at_k": {str(k): v for k, v in m.hits_at_k.items()},
                "recall_at_k": {str(k): v for k, v in m.recall_at_k.items()},
            }
            for m in report.article_metrics
        ],
    }
    out_path = out_dir / filename
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path
