from __future__ import annotations

import re

from vinculante.domain.entities import Proposal, Section


def _article_pattern(title: str) -> re.Pattern:
    m = re.match(r"Art[íi]culo\s+(\d+)", title, re.IGNORECASE)
    if m:
        num = m.group(1)
        return re.compile(rf"Art[íi]culo\s+{num}\b", re.IGNORECASE)
    return re.compile(re.escape(title), re.IGNORECASE)


def resolve_articles(
    sections: list[Section],
    article_titles: list[str],
) -> dict[str, list[int]]:
    """Map each article title to the list of section IDs whose text contains that article."""
    result: dict[str, list[int]] = {}
    for title in article_titles:
        pattern = _article_pattern(title)
        result[title] = [s.id for s in sections if pattern.search(s.text)]
    return result


def resolve_proposals(
    proposals: list[Proposal],
    refs: list[str],
) -> dict[str, int]:
    """Map reference string → proposal id."""
    ref_map = {p.reference: p.id for p in proposals if p.reference}
    return {ref: ref_map[ref] for ref in refs if ref in ref_map}
