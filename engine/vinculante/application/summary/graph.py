import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from vinculante.domain.entities import Match, Proposal, Section
from vinculante.infrastructure.config.settings import Settings

from .formatter import format_summary
from .inputs import (
    anonymise_author,
    curate_stats,
    find_orphan_sections,
    find_unmatched_proposals_with_ninguno,
    format_curated_stats,
    format_matches_for_highlights,
    format_matches_for_themes,
    format_orphan_sections,
    format_sections_for_overview,
    format_unmatched_proposals,
)
from .prompts import get_prompt
from .schemas import (
    DocumentOverview,
    GapAnalysis,
    HighlightExtraction,
    Synthesis,
    ThemeAnalysis,
)

logger = logging.getLogger(__name__)


class SummaryState(TypedDict, total=False):
    target_id: int
    target_meta: dict
    sections: list[Section]
    proposals: list[Proposal]
    accepted_matches: list[Match]
    highlight_candidates: list[Match]
    unmatched_with_ninguno: list[dict]
    orphan_sections: list[Section]
    author_labels: dict[int, str]
    curated_stats: dict

    document_overview: DocumentOverview | None
    themes: ThemeAnalysis | None
    highlights: HighlightExtraction | None
    gaps: GapAnalysis | None
    synthesis: Synthesis | None

    final_markdown: str


def build_summary_graph(
    section_repo, match_repo, proposal_repo, target_repo, llm, settings: Settings
):
    PROMPT_VERSION = settings.summary_prompt_version

    overview_llm = llm.with_structured_output(DocumentOverview)
    themes_llm = llm.with_structured_output(ThemeAnalysis)
    highlights_llm = llm.with_structured_output(HighlightExtraction)
    gaps_llm = llm.with_structured_output(GapAnalysis)
    synthesis_llm = llm.with_structured_output(Synthesis)

    OVERVIEW_PROMPT = get_prompt("document_overview", PROMPT_VERSION)
    THEMES_PROMPT = get_prompt("themes", PROMPT_VERSION)
    HIGHLIGHTS_PROMPT = get_prompt("highlights", PROMPT_VERSION)
    GAPS_PROMPT = get_prompt("gaps", PROMPT_VERSION)
    SYNTHESIZE_PROMPT = get_prompt("synthesize", PROMPT_VERSION)

    async def load_inputs(state: SummaryState) -> dict:
        target_id = state["target_id"]
        target = target_repo.get_by_id(target_id)
        if not target:
            raise ValueError(f"Target document {target_id} not found")

        sections = section_repo.get_by_target(target_id)
        all_matches = match_repo.get_by_target(target_id)
        proposals = proposal_repo.get_by_target(target_id)

        accepted = [m for m in all_matches if m.degree in ("alto", "medio")]

        author_labels: dict[int, str] = {}
        for p in proposals:
            author_labels[p.id] = anonymise_author(p.author, p.author_type)

        highlight_candidates = [
            m for m in accepted
            if m.section_spans
        ]
        orphans = find_orphan_sections(sections, accepted)
        unmatched = find_unmatched_proposals_with_ninguno(proposals, all_matches)

        # Annotate unmatched proposals with author labels
        for item in unmatched:
            p: Proposal = item["proposal"]
            item["author_label"] = author_labels.get(p.id, "propuesta ciudadana")

        stats = target.stats or {}
        return {
            "target_meta": {
                "title": target.title,
                "author": target.author,
                "date": str(target.date) if target.date else None,
                "version": target.version,
            },
            "sections": sections,
            "proposals": proposals,
            "accepted_matches": accepted,
            "highlight_candidates": highlight_candidates,
            "unmatched_with_ninguno": unmatched,
            "orphan_sections": orphans,
            "author_labels": author_labels,
            "curated_stats": curate_stats(stats),
        }

    async def analyze_document_overview(state: SummaryState) -> dict:
        meta = state["target_meta"]
        version_line = f"**Versión:** {meta['version']}" if meta.get("version") else ""
        sections_block = format_sections_for_overview(state["sections"])
        prompt = OVERVIEW_PROMPT.format(
            title=meta["title"],
            author=meta["author"],
            version_line=version_line,
            sections_block=sections_block,
        )
        try:
            result = await overview_llm.ainvoke(prompt)
            return {"document_overview": result}
        except Exception:
            logger.warning("document_overview node failed", exc_info=True)
            return {"document_overview": None}

    async def analyze_themes(state: SummaryState) -> dict:
        overview = state.get("document_overview")
        overview_text = overview.intro if overview else "(contexto no disponible)"
        matches_block = format_matches_for_themes(
            state["accepted_matches"],
            state["sections"],
            state["proposals"],
            state["author_labels"],
        )
        prompt = THEMES_PROMPT.format(
            document_overview=overview_text,
            matches_block=matches_block,
        )
        try:
            result = await themes_llm.ainvoke(prompt)
            return {"themes": result}
        except Exception:
            logger.warning("analyze_themes node failed", exc_info=True)
            return {"themes": None}

    async def extract_highlights(state: SummaryState) -> dict:
        themes = state.get("themes")
        themes_block = (
            "\n".join(f"- **{c.label}**: {c.description}" for c in themes.clusters)
            if themes and themes.clusters
            else "(sin áreas temáticas identificadas)"
        )
        highlights_block = format_matches_for_highlights(
            state["highlight_candidates"],
            state["sections"],
            state["proposals"],
            state["author_labels"],
        )
        if not highlights_block:
            return {"highlights": None}
        prompt = HIGHLIGHTS_PROMPT.format(
            themes_block=themes_block,
            highlights_block=highlights_block,
        )
        try:
            result = await highlights_llm.ainvoke(prompt)
            return {"highlights": result}
        except Exception:
            logger.warning("extract_highlights node failed", exc_info=True)
            return {"highlights": None}

    async def analyze_gaps(state: SummaryState) -> dict:
        themes = state.get("themes")
        themes_block = (
            "\n".join(f"- **{c.label}**: {c.description}" for c in themes.clusters)
            if themes and themes.clusters
            else "(sin áreas temáticas identificadas)"
        )
        orphan_block = format_orphan_sections(state["orphan_sections"])
        unmatched_block = format_unmatched_proposals(state["unmatched_with_ninguno"])
        prompt = GAPS_PROMPT.format(
            themes_block=themes_block,
            orphan_sections_block=orphan_block,
            unmatched_proposals_block=unmatched_block,
        )
        try:
            result = await gaps_llm.ainvoke(prompt)
            return {"gaps": result}
        except Exception:
            logger.warning("analyze_gaps node failed", exc_info=True)
            return {"gaps": None}

    async def synthesize(state: SummaryState) -> dict:
        overview = state.get("document_overview")
        themes = state.get("themes")
        gaps = state.get("gaps")
        themes_block = (
            "\n".join(f"- **{c.label}**: {c.description}" for c in themes.clusters)
            if themes and themes.clusters
            else "(sin áreas temáticas identificadas)"
        )
        prompt = SYNTHESIZE_PROMPT.format(
            overview_intro=overview.intro if overview else "(no disponible)",
            themes_block=themes_block,
            gaps_narrative=gaps.gaps_narrative if gaps else "(no disponible)",
            stats_block=format_curated_stats(state.get("curated_stats", {})),
        )
        try:
            result = await synthesis_llm.ainvoke(prompt)
            return {"synthesis": result}
        except Exception:
            logger.warning("synthesize node failed", exc_info=True)
            return {"synthesis": None}

    async def format_markdown(state: SummaryState) -> dict:
        md = format_summary(
            overview=state.get("document_overview"),
            themes=state.get("themes"),
            highlights=state.get("highlights"),
            gaps=state.get("gaps"),
            synthesis=state.get("synthesis"),
        )
        return {"final_markdown": md}

    workflow = StateGraph(SummaryState)
    workflow.add_node("load_inputs", load_inputs)
    workflow.add_node("analyze_document_overview", analyze_document_overview)
    workflow.add_node("analyze_themes", analyze_themes)
    workflow.add_node("extract_highlights", extract_highlights)
    workflow.add_node("analyze_gaps", analyze_gaps)
    workflow.add_node("synthesize", synthesize)
    workflow.add_node("format_markdown", format_markdown)

    workflow.add_edge(START, "load_inputs")
    workflow.add_edge("load_inputs", "analyze_document_overview")
    workflow.add_edge("analyze_document_overview", "analyze_themes")
    workflow.add_edge("analyze_themes", "extract_highlights")
    workflow.add_edge("extract_highlights", "analyze_gaps")
    workflow.add_edge("analyze_gaps", "synthesize")
    workflow.add_edge("synthesize", "format_markdown")
    workflow.add_edge("format_markdown", END)

    return workflow.compile()
