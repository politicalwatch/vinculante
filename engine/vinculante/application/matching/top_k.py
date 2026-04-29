from vinculante.infrastructure.config.settings import Settings


def compute_top_k(n_matchable_sections: int, settings: Settings) -> int:
    raw = int(n_matchable_sections * settings.matching_top_k_pct)
    return max(settings.matching_top_k_min, min(settings.matching_top_k_max, raw))
