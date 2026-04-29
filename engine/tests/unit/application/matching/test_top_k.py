import pytest

from vinculante.application.matching.top_k import compute_top_k
from vinculante.infrastructure.config.settings import Settings


def _s(pct: float = 0.10, min_k: int = 5, max_k: int = 20) -> Settings:
    return Settings(
        db_url="postgresql+psycopg2://x:x@localhost/x",
        cache_redis_host="redis://localhost",
        matching_top_k_pct=pct,
        matching_top_k_min=min_k,
        matching_top_k_max=max_k,
    )


def test_below_floor_returns_min():
    # 3 sections × 10% = 0 → clamped to min=5
    assert compute_top_k(3, _s()) == 5


def test_in_range():
    # 100 sections × 10% = 10 → in [5, 20]
    assert compute_top_k(100, _s()) == 10


def test_at_ceiling():
    # 500 sections × 10% = 50 → clamped to max=20
    assert compute_top_k(500, _s()) == 20


def test_zero_sections_returns_min():
    assert compute_top_k(0, _s()) == 5


def test_custom_clamps():
    assert compute_top_k(10, _s(pct=0.50, min_k=3, max_k=8)) == 5   # 10*0.5=5, in [3,8]
    assert compute_top_k(1,  _s(pct=0.50, min_k=3, max_k=8)) == 3   # floor
    assert compute_top_k(30, _s(pct=0.50, min_k=3, max_k=8)) == 8   # ceiling
