import asyncio

from tqdm import tqdm

from vinculante.domain.entities import Match, MatchStatus
from vinculante.domain.ports.embeddings import EmbedderProtocol
from vinculante.domain.ports.llm import LLMProvider
from vinculante.domain.ports.repositories import (
    MatchRepositoryProtocol,
    ProposalRepositoryProtocol,
    SectionRepositoryProtocol,
)
from vinculante.infrastructure.config.settings import Settings

from .graph import build_matching_graph
from .grounding import verify_quotes


class MatcherService:
    """Matches proposals to sections using vector similarity + LLM reasoning."""

    def __init__(
        self,
        proposal_repo: ProposalRepositoryProtocol,
        section_repo: SectionRepositoryProtocol,
        match_repo: MatchRepositoryProtocol,
        embedder: EmbedderProtocol,
        llm: LLMProvider,
        settings: Settings,
    ) -> None:
        self.proposal_repo = proposal_repo
        self.match_repo = match_repo
        self._settings = settings
        self._graph = build_matching_graph(section_repo, embedder, llm, settings)

    def run(self, target_id: int, skip_matched: bool = False) -> list[Match]:
        return asyncio.run(self._run_async(target_id, skip_matched))

    async def _run_async(self, target_id: int, skip_matched: bool) -> list[Match]:
        proposals = self.proposal_repo.get_by_target(target_id)
        if skip_matched:
            proposals = [p for p in proposals if not self.match_repo.get_by_proposal(p.id)]

        all_matches: list[Match] = []
        for proposal in tqdm(proposals, desc="matching", unit="proposal"):
            result = await self._graph.ainvoke(
                {
                    "proposal_id": proposal.id,
                    "proposal_text": proposal.text,
                    "target_id": target_id,
                    "candidates": [],
                    "scores": [],
                }
            )
            to_save: list[Match] = []
            candidates = result.get("candidates", [])
            scores = result.get("scores", [])
            for cand, score in zip(candidates, scores, strict=False):
                if score is None:
                    continue
                degree = score.degree
                explanation = (score.explanation or "").replace("\x00", "")
                spans: list[tuple[int, int]] | None = None
                if degree != "ninguno":
                    verified = verify_quotes(score.evidence_quotes, cand["section_text"])
                    if not verified:
                        degree = "ninguno"
                        preview = (score.evidence_quotes[0][:80] if score.evidence_quotes else "")
                        explanation = f"[grounding failed: {preview!r}] {explanation}"
                    else:
                        spans = verified
                to_save.append(Match(
                    proposal_id=proposal.id,
                    section_id=cand["id"],
                    degree=degree,
                    explanation=explanation,
                    confidence=score.confidence,
                    status=MatchStatus.pending,
                    section_spans=[list(s) for s in spans] if spans else None,
                ))
            if to_save:
                self.match_repo.bulk_save(to_save)
            all_matches.extend(to_save)
        return all_matches
