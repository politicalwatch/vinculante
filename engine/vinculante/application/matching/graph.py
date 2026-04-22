import asyncio
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from vinculante.infrastructure.config.settings import Settings

from .prompts import MATCH_PROMPT
from .schemas import MatchScore


class CandidateDict(TypedDict):
    id: int
    text: str
    section_text: str


class MatchingState(TypedDict):
    proposal_id: int
    proposal_text: str
    target_id: int
    candidates: list[CandidateDict]
    scores: list


def build_matching_graph(section_repo, embedder, llm, settings: Settings):
    structured_llm = llm.with_structured_output(MatchScore)

    async def retrieve(state: MatchingState) -> dict:
        embedding = embedder.embed_query(state["proposal_text"])
        sections = section_repo.find_similar(
            embedding,
            target_id=state["target_id"],
            k=settings.matching_top_k,
        )
        candidates: list[CandidateDict] = [
            {"id": s.id, "text": s.plain_text or s.text, "section_text": s.text}
            for s in sections
        ]
        return {"candidates": candidates}

    async def _score_one(
        candidate: CandidateDict,
        proposal_text: str,
        semaphore: asyncio.Semaphore,
    ) -> MatchScore | None:
        prompt = MATCH_PROMPT.format(
            proposal_text=proposal_text,
            section_text=candidate["text"],
        )
        async with semaphore:
            try:
                return await structured_llm.ainvoke(prompt)
            except Exception:
                return None

    async def score(state: MatchingState) -> dict:
        semaphore = asyncio.Semaphore(settings.matching_concurrency)
        scores = await asyncio.gather(
            *[_score_one(c, state["proposal_text"], semaphore) for c in state["candidates"]]
        )
        return {"scores": list(scores)}

    workflow = StateGraph(MatchingState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("score", score)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "score")
    workflow.add_edge("score", END)

    return workflow.compile()
