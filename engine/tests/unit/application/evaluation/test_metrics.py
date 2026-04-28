import pytest

from vinculante.application.evaluation.metrics import (
    AggregateMetrics,
    per_article_breakdown,
    aggregate_metrics,
)

ARTICLES = ["Artículo 1. Objeto", "Artículo 2. Ámbito"]

# proposal_id, article
ALL_EXP: set[tuple[int, str]] = {
    (1, "Artículo 1. Objeto"),
    (2, "Artículo 1. Objeto"),
    (3, "Artículo 2. Ámbito"),
}


def test_perfect_match():
    metrics = per_article_breakdown(ALL_EXP, ALL_EXP, ARTICLES)
    for m in metrics:
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.f1 == 1.0


def test_no_match():
    metrics = per_article_breakdown(ALL_EXP, set(), ARTICLES)
    for m in metrics:
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1 == 0.0


def test_partial_match():
    actual = {(1, "Artículo 1. Objeto")}  # only one of two expected for art1
    metrics = per_article_breakdown(ALL_EXP, actual, ARTICLES)
    art1 = next(m for m in metrics if m.article == "Artículo 1. Objeto")
    assert art1.tp == 1
    assert art1.fn == 1
    assert art1.fp == 0
    assert art1.recall == pytest.approx(0.5)
    assert art1.precision == 1.0


def test_false_positive():
    actual = {(99, "Artículo 2. Ámbito")}  # not in expected
    metrics = per_article_breakdown(ALL_EXP, actual, ARTICLES)
    art2 = next(m for m in metrics if m.article == "Artículo 2. Ámbito")
    assert art2.tp == 0
    assert art2.fp == 1
    assert art2.fn == 1
    assert art2.precision == 0.0
    assert art2.recall == 0.0


def test_aggregate_perfect():
    agg = aggregate_metrics(per_article_breakdown(ALL_EXP, ALL_EXP, ARTICLES), ALL_EXP, ALL_EXP)
    assert agg.micro_f1 == pytest.approx(1.0)
    assert agg.macro_f1 == pytest.approx(1.0)


def test_aggregate_empty_actual():
    art_m = per_article_breakdown(ALL_EXP, set(), ARTICLES)
    agg = aggregate_metrics(art_m, ALL_EXP, set())
    assert agg.micro_precision == 0.0
    assert agg.micro_recall == 0.0
    assert agg.micro_f1 == 0.0


def test_f1_zero_denominator():
    """Ensure no ZeroDivisionError when both precision and recall are 0."""
    art_m = per_article_breakdown(set(), set(), ARTICLES)
    agg = aggregate_metrics(art_m, set(), set())
    assert agg.micro_f1 == 0.0
    assert agg.macro_f1 == 0.0
