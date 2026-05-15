import statistics
from collections import Counter

from vinculante.domain.entities import Match, Section

ACCEPTED_DEGREES = {"alto", "medio"}


def _confidence_stats(values: list[float]) -> dict:
    if not values:
        return {"mean": None, "median": None, "p25": None, "p75": None}
    mean = round(statistics.mean(values), 4)
    median = round(statistics.median(values), 4)
    if len(values) >= 2:
        qs = statistics.quantiles(values, n=4)
        p25, p75 = round(qs[0], 4), round(qs[2], 4)
    else:
        p25 = p75 = round(values[0], 4)
    return {"mean": mean, "median": median, "p25": p25, "p75": p75}


def compute_target_stats(sections: list[Section], matches: list[Match], total_proposals: int = 0) -> dict:
    accepted = [m for m in matches if m.degree in ACCEPTED_DEGREES]
    matchable = [s for s in sections if s.is_matchable]
    n_matchable = len(matchable)
    matchable_ids = {s.id for s in matchable}

    matched_section_ids = {m.section_id for m in accepted} & matchable_ids
    n_matched = len(matched_section_ids)
    total = len(accepted)
    unique_proposals = len({m.proposal_id for m in accepted})

    # Coverage
    coverage = {
        "pct_sections_matched": round(n_matched / n_matchable, 4) if n_matchable else 0.0,
        "orphan_sections": n_matchable - n_matched,
        "total_matches": total,
        "unique_proposals": unique_proposals,
        "total_proposals": total_proposals,
    }

    # Degree distribution
    alto_count = sum(1 for m in accepted if m.degree == "alto")
    medio_count = sum(1 for m in accepted if m.degree == "medio")
    degree = {
        "alto": {"count": alto_count, "pct": round(alto_count / total, 4) if total else 0.0},
        "medio": {"count": medio_count, "pct": round(medio_count / total, 4) if total else 0.0},
    }

    # Confidence
    all_confs = [m.confidence for m in accepted if m.confidence is not None]
    alto_confs = [m.confidence for m in accepted if m.degree == "alto" and m.confidence is not None]
    medio_confs = [m.confidence for m in accepted if m.degree == "medio" and m.confidence is not None]
    confidence = {
        **_confidence_stats(all_confs),
        "by_degree": {
            "alto": _confidence_stats(alto_confs),
            "medio": _confidence_stats(medio_confs),
        },
    }

    # Distribution per section
    alto_per_section = Counter(
        m.section_id for m in accepted if m.degree == "alto" and m.section_id in matchable_ids
    )
    medio_per_section = Counter(
        m.section_id for m in accepted if m.degree == "medio" and m.section_id in matchable_ids
    )
    avg_per_matched = round(total / n_matched, 4) if n_matched else None
    per_section = [
        {
            "section_id": s.id,
            "alto": alto_per_section.get(s.id, 0),
            "medio": medio_per_section.get(s.id, 0),
        }
        for s in matchable
    ]
    distribution = {
        "avg_matches_per_matched_section": avg_per_matched,
        "per_section": per_section,
    }

    # Quality
    with_spans = sum(1 for m in accepted if m.section_spans)
    pct_with_spans = round(with_spans / total, 4) if total else 0.0
    top_proposals = [
        {"proposal_id": pid, "count": cnt}
        for pid, cnt in Counter(m.proposal_id for m in accepted).most_common(5)
    ]
    quality = {"pct_with_spans": pct_with_spans, "top_proposals": top_proposals}

    return {
        "coverage": coverage,
        "degree": degree,
        "confidence": confidence,
        "distribution": distribution,
        "quality": quality,
    }
