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
        lines += ["## Resumen de la ley", "", overview.intro, ""]
        if overview.axes:
            for axis in overview.axes:
                lines.append(f"- {axis}")
            lines.append("")

    has_synthesis = synthesis and synthesis.vision_general
    has_themes = themes and themes.clusters

    if has_synthesis or has_themes:
        lines += ["## Resumen de las vinculaciones detectadas", ""]
        if has_synthesis:
            lines += [synthesis.vision_general, ""]
        if has_themes:
            if has_synthesis:
                lines += ["Las áreas con mayor vinculación son:", ""]
            for cluster in themes.clusters:
                lines.append(f"- **{cluster.label}**: {cluster.description}")
            lines.append("")

    if highlights and (highlights.citizen_highlights or highlights.academia_highlights):
        lines += ["## Vinculaciones destacadas", ""]
        if highlights.citizen_highlights:
            if highlights.citizen_intro:
                lines += [highlights.citizen_intro, ""]
            for h in highlights.citizen_highlights:
                lines.append(
                    f"- **{h.author_label}** — {h.proposal_claim}. "
                    f"Vinculada con **{h.section_ref}**: {h.relevance}"
                )
            lines.append("")
        if highlights.academia_highlights:
            if highlights.academia_intro:
                lines += [highlights.academia_intro, ""]
            for h in highlights.academia_highlights:
                lines.append(
                    f"- **{h.author_label}** — {h.proposal_claim}. "
                    f"Vinculada con **{h.section_ref}**: {h.relevance}"
                )
            lines.append("")

    has_gaps = gaps and any([
        gaps.orphan_observations,
        gaps.citizen_unmatched,
        gaps.academia_unmatched,
        gaps.gaps_narrative,
    ])
    if has_gaps:
        lines += ["## Propuestas no recogidas", ""]
        if gaps.orphan_observations:
            lines += [gaps.orphan_observations, ""]
        if gaps.citizen_unmatched:
            lines += [gaps.citizen_unmatched, ""]
        if gaps.academia_unmatched:
            lines += [gaps.academia_unmatched, ""]
        if gaps.gaps_narrative:
            lines += [gaps.gaps_narrative, ""]

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
