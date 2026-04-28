from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArticleMetrics:
    article: str
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


@dataclass
class AggregateMetrics:
    micro_precision: float
    micro_recall: float
    micro_f1: float
    macro_precision: float
    macro_recall: float
    macro_f1: float


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def per_article_breakdown(
    expected_pairs: set[tuple[int, str]],
    actual_pairs: set[tuple[int, str]],
    articles: list[str],
) -> list[ArticleMetrics]:
    result = []
    for article in articles:
        exp = {pid for pid, a in expected_pairs if a == article}
        act = {pid for pid, a in actual_pairs if a == article}
        tp = len(exp & act)
        fp = len(act - exp)
        fn = len(exp - act)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        result.append(ArticleMetrics(article=article, tp=tp, fp=fp, fn=fn, precision=p, recall=r, f1=_f1(p, r)))
    return result


def aggregate_metrics(
    article_metrics: list[ArticleMetrics],
    all_expected: set[tuple[int, str]],
    all_actual: set[tuple[int, str]],
) -> AggregateMetrics:
    tp = len(all_expected & all_actual)
    fp = len(all_actual - all_expected)
    fn = len(all_expected - all_actual)

    micro_p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    micro_r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    macro_p = sum(m.precision for m in article_metrics) / len(article_metrics) if article_metrics else 0.0
    macro_r = sum(m.recall for m in article_metrics) / len(article_metrics) if article_metrics else 0.0

    return AggregateMetrics(
        micro_precision=micro_p,
        micro_recall=micro_r,
        micro_f1=_f1(micro_p, micro_r),
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=_f1(macro_p, macro_r),
    )
