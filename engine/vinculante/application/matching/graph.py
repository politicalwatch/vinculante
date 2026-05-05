import asyncio
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from vinculante.infrastructure.config.settings import Settings

from .prompts import get_prompt
from .schemas import (
    CandidateClassification,
    MatchScore,
    OneToManyMatchResults,
    ProposalAnalysis,
)


class CandidateDict(TypedDict):
    id: int
    section_text: str


class MatchingState(TypedDict):
    proposal_id: int
    proposal_text: str
    target_id: int
    effective_top_k: int
    candidates: list[CandidateDict]
    scores: list
    # Pipeline specific
    analysis: ProposalAnalysis | None
    classification: CandidateClassification | None


def build_matching_graph(section_repo, embedder, llm, settings: Settings):
    if settings.matching_strategy == "one-to-many":
        return _build_one_to_many_graph(section_repo, embedder, llm, settings)
    if settings.matching_strategy == "pipeline":
        return _build_pipeline_graph(section_repo, embedder, llm, settings)
    if settings.matching_strategy == "one-to-many-critic":
        return _build_one_to_many_critic_graph(section_repo, embedder, llm, settings)
    return _build_one_to_one_graph(section_repo, embedder, llm, settings)


def _build_one_to_one_graph(section_repo, embedder, llm, settings: Settings):
    structured_llm = llm.with_structured_output(MatchScore)
    MATCH_PROMPT = get_prompt(settings.matching_prompt_version, one_to_many=False)

    async def retrieve(state: MatchingState) -> dict:
        embedding = embedder.embed_query(state["proposal_text"])
        sections = section_repo.find_similar(
            embedding,
            target_id=state["target_id"],
            k=state["effective_top_k"],
        )
        candidates: list[CandidateDict] = [
            {"id": s.id, "section_text": s.text}
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
            section_text=candidate["section_text"],
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


def _build_one_to_many_graph(section_repo, embedder, llm, settings: Settings):
    structured_llm = llm.with_structured_output(OneToManyMatchResults)
    MATCH_PROMPT = get_prompt(settings.matching_prompt_version, one_to_many=True)

    async def retrieve(state: MatchingState) -> dict:
        embedding = embedder.embed_query(state["proposal_text"])
        sections = section_repo.find_similar(
            embedding,
            target_id=state["target_id"],
            k=state["effective_top_k"],
        )
        candidates: list[CandidateDict] = [
            {"id": s.id, "section_text": s.text}
            for s in sections
        ]
        return {"candidates": candidates}

    async def score(state: MatchingState) -> dict:
        if not state["candidates"]:
            return {"scores": []}

        candidates_block = "\n\n".join(
            [f"--- ID: {c['id']} ---\n{c['section_text']}" for c in state["candidates"]]
        )
        prompt = MATCH_PROMPT.format(
            proposal_text=state["proposal_text"],
            candidates_text=candidates_block,
        )

        try:
            results = await structured_llm.ainvoke(prompt)
            # Map results back to the order of candidates
            scores_map = {m.section_id: m for m in results.matches}
            ordered_scores = [scores_map.get(c["id"]) for c in state["candidates"]]
            return {"scores": ordered_scores}
        except Exception:
            return {"scores": [None] * len(state["candidates"])}

    workflow = StateGraph(MatchingState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("score", score)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "score")
    workflow.add_edge("score", END)

    return workflow.compile()


def _build_pipeline_graph(section_repo, embedder, llm, settings: Settings):
    # Specialized structured LLMs
    proposal_analyzer = llm.with_structured_output(ProposalAnalysis)
    candidate_classifier = llm.with_structured_output(CandidateClassification)
    scorer = llm.with_structured_output(MatchScore)

    # Prompts
    ANALYZE_PROPOSAL = get_prompt("", pipeline_step="analyze_proposal")
    CLASSIFY_CANDIDATES = get_prompt("", pipeline_step="classify_candidates")
    SCORE_CANDIDATE = get_prompt("", pipeline_step="score_candidate")

    async def retrieve(state: MatchingState) -> dict:
        embedding = embedder.embed_query(state["proposal_text"])
        sections = section_repo.find_similar(
            embedding,
            target_id=state["target_id"],
            k=state["effective_top_k"],
        )
        candidates: list[CandidateDict] = [
            {"id": s.id, "section_text": s.text}
            for s in sections
        ]
        return {"candidates": candidates}

    async def analyze_proposal(state: MatchingState) -> dict:
        analysis = await proposal_analyzer.ainvoke(
            ANALYZE_PROPOSAL.format(proposal_text=state["proposal_text"])
        )
        return {"analysis": analysis}

    async def classify_candidates(state: MatchingState) -> dict:
        candidates_block = "\n\n".join(
            [f"--- ID: {c['id']} ---\n{c['section_text']}" for c in state["candidates"]]
        )
        classification = await candidate_classifier.ainvoke(
            CLASSIFY_CANDIDATES.format(candidates_text=candidates_block)
        )
        return {"classification": classification}

    async def score_pipeline(state: MatchingState) -> dict:
        analysis = state["analysis"]
        classification = state["classification"]
        scores_map: dict[int, MatchScore] = {}

        # 1. Target candidate IDs
        op_ids = classification.operative_ids
        intro_ids = classification.introductory_ids

        # 2. Strategy: Score operative first
        op_candidates = [c for c in state["candidates"] if c["id"] in op_ids]
        
        async def _score_one_pipeline(cand: CandidateDict) -> tuple[int, MatchScore | None]:
            prompt = SCORE_CANDIDATE.format(
                core_demand=analysis.core_demand,
                domain=analysis.domain,
                section_text=cand["section_text"],
            )
            try:
                res = await scorer.ainvoke(prompt)
                return cand["id"], res
            except Exception:
                return cand["id"], None

        op_results = await asyncio.gather(*[_score_one_pipeline(c) for c in op_candidates])
        for cid, score in op_results:
            if score:
                scores_map[cid] = score

        # 3. Exclusivity Rule: If we have strong operative matches, ignore introductory
        has_strong_op = any(s.degree in ["alto", "medio"] for s in scores_map.values())
        
        if not has_strong_op:
            intro_candidates = [c for c in state["candidates"] if c["id"] in intro_ids]
            intro_results = await asyncio.gather(*[_score_one_pipeline(c) for c in intro_candidates])
            for cid, score in intro_results:
                if score:
                    scores_map[cid] = score
        else:
            # Mark introductory as 'ninguno' explicitly
            for cid in intro_ids:
                scores_map[cid] = MatchScore(
                    degree="ninguno",
                    explanation="Descartado por la regla de exclusividad: ya existe una vinculación operativa más específica.",
                    confidence=1.0,
                    evidence_quotes=[]
                )

        # Map back to ordered candidates
        ordered_scores = [scores_map.get(c["id"]) for c in state["candidates"]]
        return {"scores": ordered_scores}

    workflow = StateGraph(MatchingState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("analyze_proposal", analyze_proposal)
    workflow.add_node("classify_candidates", classify_candidates)
    workflow.add_node("score", score_pipeline)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "analyze_proposal")
    workflow.add_edge("analyze_proposal", "classify_candidates")
    workflow.add_edge("classify_candidates", "score")
    workflow.add_edge("score", END)

    return workflow.compile()


def _build_one_to_many_critic_graph(section_repo, embedder, llm, settings: Settings):
    scorer_llm = llm.with_structured_output(OneToManyMatchResults)
    critic_llm = llm.with_structured_output(OneToManyMatchResults)
    SCORE_PROMPT = get_prompt(settings.matching_prompt_version, one_to_many=True)
    CRITIC_PROMPT = get_prompt("", critic_version=settings.matching_critic_prompt_version)

    async def retrieve(state: MatchingState) -> dict:
        embedding = embedder.embed_query(state["proposal_text"])
        sections = section_repo.find_similar(
            embedding,
            target_id=state["target_id"],
            k=state["effective_top_k"],
        )
        candidates: list[CandidateDict] = [
            {"id": s.id, "section_text": s.text}
            for s in sections
        ]
        return {"candidates": candidates}

    async def score(state: MatchingState) -> dict:
        if not state["candidates"]:
            return {"scores": []}

        candidates_block = "\n\n".join(
            [f"--- ID: {c['id']} ---\n{c['section_text']}" for c in state["candidates"]]
        )
        prompt = SCORE_PROMPT.format(
            proposal_text=state["proposal_text"],
            candidates_text=candidates_block,
        )

        try:
            results = await scorer_llm.ainvoke(prompt)
            scores_map = {m.section_id: m for m in results.matches}
            ordered_scores = [scores_map.get(c["id"]) for c in state["candidates"]]
            return {"scores": ordered_scores}
        except Exception:
            return {"scores": [None] * len(state["candidates"])}

    async def critique(state: MatchingState) -> dict:
        if not state["candidates"] or not state["scores"]:
            return {}

        candidates_block = "\n\n".join(
            f"--- ID: {c['id']} | current: {s.degree if s else 'ninguno'} ---\n"
            f"{c['section_text']}\nRazonamiento previo: {s.explanation if s else '—'}"
            for c, s in zip(state["candidates"], state["scores"], strict=False)
        )
        prompt = CRITIC_PROMPT.format(
            proposal_text=state["proposal_text"],
            candidates_block=candidates_block,
        )

        try:
            revised = await critic_llm.ainvoke(prompt)
            scores_map = {m.section_id: m for m in revised.matches}
            prev_map = {s.section_id: s for s in state["scores"] if s}
            merged = []
            for c in state["candidates"]:
                prev = prev_map.get(c["id"])
                critic = scores_map.get(c["id"])
                if prev is None or critic is None:
                    merged.append(prev)
                    continue
                # Promotion: scorer rejected, critic shows — use critic's explanation
                # as scorer's "not relevant" reasoning would contradict the new degree.
                is_promotion = (
                    prev.degree in {"ninguno", "bajo"}
                    and critic.degree in {"alto", "medio"}
                )
                if is_promotion:
                    merged.append(critic)
                else:
                    merged.append(critic.model_copy(update={"explanation": prev.explanation}))
            return {"scores": merged}
        except Exception:
            return {}

    workflow = StateGraph(MatchingState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("score", score)
    workflow.add_node("critique", critique)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "score")
    workflow.add_edge("score", "critique")
    workflow.add_edge("critique", END)

    return workflow.compile()
