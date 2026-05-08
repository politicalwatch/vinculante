from collections import defaultdict
from typing import Literal

from vinculante.domain.entities import Match, Proposal, Section

_CITIZEN_TYPES = {"citizen"}
_SECTION_OVERVIEW_MAX_CHARS = 800
_NINGUNO_EXPLANATION_MAX_CHARS = 300
_ORPHAN_MIN_TEXT_LENGTH = 100
_UNMATCHED_MIN_TEXT_LENGTH = 80
_NINGUNO_MIN_EXPLANATION_LENGTH = 30
_SECTION_TITLE_MAX_CHARS = 120


def _derive_section_title(section: Section) -> str | None:
    raw = (section.text_markdown or section.text or "").strip()
    if not raw:
        return None
    first_line = raw.split("\n", 1)[0].strip().lstrip("#").strip()
    if len(first_line) > 100:
        for sep in (". ", "; "):
            if sep in first_line:
                first_line = first_line.split(sep, 1)[0].strip()
                break
    if len(first_line) > _SECTION_TITLE_MAX_CHARS:
        first_line = first_line[:_SECTION_TITLE_MAX_CHARS - 3].rstrip() + "…"
    return first_line or None


def classify_author_type(
    author_type: str | None,
) -> Literal["citizen", "academia"] | None:
    if not author_type:
        return None
    normalized = author_type.strip().lower()
    if normalized == "citizen":
        return "citizen"
    if normalized == "academia":
        return "academia"
    return None


def anonymise_author(author: str | None, author_type: str | None) -> str:
    if not author_type:
        return "propuesta ciudadana"
    if classify_author_type(author_type) == "citizen":
        return "propuesta ciudadana"
    return author or "propuesta ciudadana"


def find_orphan_sections(sections: list[Section], accepted_matches: list[Match]) -> list[Section]:
    matched_ids = {m.section_id for m in accepted_matches}
    return [
        s for s in sections
        if s.is_matchable
        and s.id not in matched_ids
        and s.text
        and len(s.text) >= _ORPHAN_MIN_TEXT_LENGTH
    ]


def find_unmatched_proposals_with_ninguno(
    proposals: list[Proposal],
    all_matches: list[Match],
) -> list[dict]:
    accepted_ids = {m.proposal_id for m in all_matches if m.degree in ("alto", "medio")}
    ninguno_by_proposal: dict[int, list[Match]] = defaultdict(list)
    for m in all_matches:
        if m.degree == "ninguno":
            ninguno_by_proposal[m.proposal_id].append(m)

    result = []
    for p in proposals:
        if classify_author_type(p.author_type) is None:
            continue
        if p.id in accepted_ids:
            continue
        if not p.text or len(p.text) < _UNMATCHED_MIN_TEXT_LENGTH:
            continue
        # Pick highest-confidence ninguno with a non-trivial explanation
        ninguno_sorted = sorted(
            ninguno_by_proposal.get(p.id, []), key=lambda m: -(m.confidence or 0.0)
        )
        representative: str | None = None
        for m in ninguno_sorted:
            if m.explanation and len(m.explanation) >= _NINGUNO_MIN_EXPLANATION_LENGTH:
                representative = m.explanation[:_NINGUNO_EXPLANATION_MAX_CHARS]
                break
        result.append({"proposal": p, "representative_ninguno": representative})
    return result


def curate_stats(stats: dict) -> dict:
    coverage = stats.get("coverage", {})
    degree = stats.get("degree", {})
    distribution = stats.get("distribution", {})
    quality = stats.get("quality", {})
    return {
        "pct_sections_matched": coverage.get("pct_sections_matched"),
        "orphan_sections_count": coverage.get("orphan_sections"),
        "avg_matches_per_matched_section": distribution.get("avg_matches_per_matched_section"),
        "alto_count": degree.get("alto", {}).get("count"),
        "medio_count": degree.get("medio", {}).get("count"),
        "top_proposal_ids": [t["proposal_id"] for t in quality.get("top_proposals", [])],
    }


def format_sections_for_overview(sections: list[Section]) -> str:
    lines = []
    for s in sections:
        if not s.text:
            continue
        ref = f"Sección {s.section_number}" if s.section_number else f"[sección id {s.id}]"
        page = f" (p. {s.page_number})" if s.page_number else ""
        max_c = _SECTION_OVERVIEW_MAX_CHARS
        text = s.text if len(s.text) <= max_c else s.text[:max_c] + "…"
        lines.append(f"--- {ref}{page} ---\n{text}")
    return "\n\n".join(lines)


def format_matches_for_themes(
    accepted_matches: list[Match],
    sections: list[Section],
    proposals: list[Proposal],
    author_labels: dict[int, str],
) -> str:
    section_map = {s.id: s for s in sections}
    proposal_map = {p.id: p for p in proposals}
    by_section: dict[int, list[Match]] = defaultdict(list)
    for m in accepted_matches:
        by_section[m.section_id].append(m)

    lines = []
    for section_id, matches in by_section.items():
        s = section_map.get(section_id)
        if not s:
            continue
        ref = f"Sección {s.section_number}" if s.section_number else f"[id {s.id}]"
        page = f" (p. {s.page_number})" if s.page_number else ""
        lines.append(f"=== {ref}{page} ===")
        for m in matches:
            p = proposal_map.get(m.proposal_id)
            if not p or classify_author_type(p.author_type) is None:
                continue
            author = author_labels.get(p.id, "propuesta ciudadana")
            lines.append(f"  [{m.degree.upper()}] {author}: {p.text[:200]}")
            if m.explanation:
                lines.append(f"  → {m.explanation[:200]}")
        lines.append("")
    return "\n".join(lines)


def format_matches_for_highlights(
    accepted_matches: list[Match],
    sections: list[Section],
    proposals: list[Proposal],
    author_labels: dict[int, str],
) -> str:
    section_map = {s.id: s for s in sections}
    proposal_map = {p.id: p for p in proposals}

    # Deterministic signal: how many distinct sections each proposal is matched to (breadth)
    proposal_section_counts: dict[int, set[int]] = defaultdict(set)
    for m in accepted_matches:
        p = proposal_map.get(m.proposal_id)
        if not p or classify_author_type(p.author_type) is None:
            continue
        proposal_section_counts[m.proposal_id].add(m.section_id)

    citizen_entries: list[str] = []
    academia_entries: list[str] = []

    for m in accepted_matches:
        s = section_map.get(m.section_id)
        p = proposal_map.get(m.proposal_id)
        if not s or not p:
            continue
        bucket = classify_author_type(p.author_type)
        if bucket is None:
            continue
        title = _derive_section_title(s)
        if title:
            ref = title
        elif s.section_number:
            ref = f"Sección {s.section_number}"
        else:
            ref = f"[id {s.id}]"
        page = f" (p. {s.page_number})" if s.page_number else ""
        author = author_labels.get(p.id, "propuesta ciudadana")
        n_sections = len(proposal_section_counts[m.proposal_id])
        entry = (
            f"--- {ref}{page} | grado {m.degree} ---\n"
            f"Autor: {author}\n"
            f"Propuesta: {p.text}\n"
            f"Explicación: {m.explanation or '—'}\n"
            f"Señales: propuesta presente en {n_sections} {'secciones' if n_sections != 1 else 'sección'}"
        )
        if bucket == "citizen":
            citizen_entries.append(entry)
        else:
            academia_entries.append(entry)

    blocks = []
    if citizen_entries:
        blocks.append("## Propuestas ciudadanas\n\n" + "\n\n".join(citizen_entries))
    if academia_entries:
        blocks.append("## Propuestas académicas\n\n" + "\n\n".join(academia_entries))
    return "\n\n".join(blocks)


def format_orphan_sections(orphans: list[Section]) -> str:
    lines = []
    for s in orphans:
        ref = f"Sección {s.section_number}" if s.section_number else f"[id {s.id}]"
        page = f" (p. {s.page_number})" if s.page_number else ""
        excerpt = (s.text or "")[:400]
        lines.append(f"--- {ref}{page} ---\n{excerpt}")
    return "\n\n".join(lines) if lines else "(ninguna)"


def format_unmatched_proposals(unmatched: list[dict]) -> str:
    citizen_entries: list[str] = []
    academia_entries: list[str] = []

    for item in unmatched:
        p: Proposal = item["proposal"]
        bucket = classify_author_type(p.author_type)
        if bucket is None:
            continue
        ninguno: str | None = item["representative_ninguno"]
        entry_lines = [f"- {p.text}"]
        if ninguno:
            entry_lines.append(f"  (Razón de no vinculación: {ninguno})")
        entry = "\n".join(entry_lines)
        if bucket == "citizen":
            citizen_entries.append(entry)
        else:
            academia_entries.append(entry)

    blocks = []
    if citizen_entries:
        blocks.append("## Propuestas ciudadanas\n\n" + "\n".join(citizen_entries))
    if academia_entries:
        blocks.append("## Propuestas académicas\n\n" + "\n".join(academia_entries))
    return "\n\n".join(blocks) if blocks else "(ninguna)"


def format_curated_stats(stats: dict) -> str:
    pct = stats.get("pct_sections_matched")
    orphans = stats.get("orphan_sections_count")
    avg = stats.get("avg_matches_per_matched_section")
    alto = stats.get("alto_count")
    medio = stats.get("medio_count")
    lines = []
    if pct is not None:
        lines.append(f"- Cobertura: {pct:.0%} de secciones con al menos una vinculación aceptada")
    if orphans is not None:
        lines.append(f"- Secciones sin vinculación: {orphans}")
    if avg is not None:
        lines.append(f"- Media de vinculaciones por sección vinculada: {avg:.1f}")
    if alto is not None and medio is not None:
        lines.append(f"- Grado alto: {alto} vinculaciones | Grado medio: {medio} vinculaciones")
    return "\n".join(lines) if lines else "(sin datos)"
