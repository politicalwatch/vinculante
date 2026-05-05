import asyncio
import logging

from vinculante.domain.ports.llm import LLMProvider
from vinculante.domain.ports.repositories import (
    MatchRepositoryProtocol,
    ProposalRepositoryProtocol,
    SectionRepositoryProtocol,
    TargetRepositoryProtocol,
)
from vinculante.infrastructure.config.settings import Settings

from .graph import build_summary_graph

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(
        self,
        section_repo: SectionRepositoryProtocol,
        match_repo: MatchRepositoryProtocol,
        proposal_repo: ProposalRepositoryProtocol,
        target_repo: TargetRepositoryProtocol,
        llm: LLMProvider,
        settings: Settings,
    ) -> None:
        self._target_repo = target_repo
        self._graph = build_summary_graph(
            section_repo=section_repo,
            match_repo=match_repo,
            proposal_repo=proposal_repo,
            target_repo=target_repo,
            llm=llm,
            settings=settings,
        )

    def run(self, target_id: int) -> str:
        return asyncio.run(self._run_async(target_id))

    async def _run_async(self, target_id: int) -> str:
        result = await self._graph.ainvoke({"target_id": target_id})
        summary = result.get("final_markdown", "")
        if summary:
            self._target_repo.update_summary(target_id, summary)
        else:
            logger.warning("Summary generation produced empty output for target %d", target_id)
        return summary
