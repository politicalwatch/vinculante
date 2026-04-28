from __future__ import annotations

from dataclasses import dataclass, field

from vinculante.application.evaluation.metrics import (
    AggregateMetrics,
    ArticleMetrics,
    aggregate_metrics,
    per_article_breakdown,
)
from vinculante.application.evaluation.resolver import resolve_articles, resolve_proposals
from vinculante.application.evaluation.testset import EvalCase
from vinculante.infrastructure.db.repositories.matches import MatchRepository
from vinculante.infrastructure.db.repositories.proposals import ProposalRepository
from vinculante.infrastructure.db.repositories.sections import SectionRepository

_DEGREE_RANK: dict[str, int] = {"ninguno": 0, "bajo": 1, "medio": 2, "alto": 3}


def _excluded_degrees(min_degree: str) -> tuple[str, ...]:
    threshold = _DEGREE_RANK.get(min_degree, 1)
    return tuple(d for d, rank in _DEGREE_RANK.items() if rank < threshold)


@dataclass
class RawMatch:
    proposal_id: int
    section_id: int
    degree: str
    confidence: float | None


@dataclass
class Diagnostics:
    unmapped_articles: list[str]
    unmapped_refs: list[str]
    unrelated_matches: int


@dataclass
class EvaluationReport:
    domain: str
    target_id: int
    article_metrics: list[ArticleMetrics]
    aggregate: AggregateMetrics
    diagnostics: Diagnostics
    raw_matches: list[RawMatch] = field(default_factory=list)


class EvaluatorService:
    def __init__(
        self,
        section_repo: SectionRepository,
        proposal_repo: ProposalRepository,
        match_repo: MatchRepository,
    ) -> None:
        self.section_repo = section_repo
        self.proposal_repo = proposal_repo
        self.match_repo = match_repo

    def evaluate(
        self,
        case: EvalCase,
        target_id: int,
        min_confidence: float = 0.0,
        min_degree: str = "bajo",
    ) -> EvaluationReport:
        sections = self.section_repo.get_by_target(target_id)
        proposals = self.proposal_repo.get_by_target(target_id)

        # Fetch all non-ninguno matches for the run JSON record
        all_matches = self.match_repo.get_accepted_by_target(
            target_id,
            min_confidence=min_confidence,
            excluded_degrees=("ninguno",),
        )

        # Filter by min_degree for metric calculation
        excluded = _excluded_degrees(min_degree)
        matches = [m for m in all_matches if m.degree not in excluded]

        article_titles = [e.article for e in case.expected]
        article_section_map = resolve_articles(sections, article_titles)

        all_refs = [ref for e in case.expected for ref in e.proposal_refs]
        ref_proposal_map = resolve_proposals(proposals, all_refs)

        unmapped_articles = [a for a, sids in article_section_map.items() if not sids]
        unmapped_refs = [ref for ref in all_refs if ref not in ref_proposal_map]

        expected_pairs: set[tuple[int, str]] = set()
        for entry in case.expected:
            for ref in entry.proposal_refs:
                pid = ref_proposal_map.get(ref)
                if pid is not None:
                    expected_pairs.add((pid, entry.article))

        section_to_article: dict[int, str] = {}
        for article, sec_ids in article_section_map.items():
            for sid in sec_ids:
                section_to_article[sid] = article

        actual_pairs: set[tuple[int, str]] = set()
        unrelated = 0
        for match in matches:
            article = section_to_article.get(match.section_id)
            if article:
                actual_pairs.add((match.proposal_id, article))
            else:
                unrelated += 1

        art_metrics = per_article_breakdown(expected_pairs, actual_pairs, article_titles)
        agg = aggregate_metrics(art_metrics, expected_pairs, actual_pairs)

        raw_matches = [
            RawMatch(
                proposal_id=m.proposal_id,
                section_id=m.section_id,
                degree=m.degree or "ninguno",
                confidence=m.confidence,
            )
            for m in all_matches
        ]

        return EvaluationReport(
            domain=case.domain,
            target_id=target_id,
            article_metrics=art_metrics,
            aggregate=agg,
            diagnostics=Diagnostics(
                unmapped_articles=unmapped_articles,
                unmapped_refs=unmapped_refs,
                unrelated_matches=unrelated,
            ),
            raw_matches=raw_matches,
        )
