from .schemas import DocumentOverview, GapAnalysis, HighlightExtraction, Synthesis, ThemeAnalysis


def format_summary(
    overview: DocumentOverview | None,
    themes: ThemeAnalysis | None,
    highlights: HighlightExtraction | None,
    gaps: GapAnalysis | None,
    synthesis: Synthesis | None,
) -> str:
    lines: list[str] = []

    if overview:
        lines += ["## Principales ejes", "", overview.intro, ""]
        if overview.axes:
            for axis in overview.axes:
                lines.append(f"- {axis}")
            lines.append("")

    if synthesis and synthesis.vision_general:
        lines += ["## Visión general", "", synthesis.vision_general, ""]

    if themes and themes.clusters:
        lines += ["## Áreas de mayor vinculación", ""]
        for cluster in themes.clusters:
            lines.append(f"- **{cluster.label}**: {cluster.description}")
        lines.append("")

    if highlights and highlights.highlights:
        lines += ["## Vinculaciones destacadas", ""]
        for h in highlights.highlights:
            lines.append(
                f"- **{h.author_label}** — {h.proposal_claim}. "
                f"Vinculada con **{h.section_ref}**: {h.relevance}"
            )
        lines.append("")

    has_gaps = gaps and any(
        [gaps.orphan_observations, gaps.unmatched_clusters, gaps.gaps_narrative]
    )
    if has_gaps:
        lines += ["## Lagunas detectadas", ""]
        if gaps.orphan_observations:
            lines += [gaps.orphan_observations, ""]
        if gaps.unmatched_clusters:
            lines += [gaps.unmatched_clusters, ""]
        if gaps.gaps_narrative:
            lines += [gaps.gaps_narrative, ""]

    if synthesis and synthesis.observaciones:
        lines += ["## Observaciones", ""]
        for obs in synthesis.observaciones:
            lines.append(f"- {obs}")
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
