from .critic import v1 as c_v1, v2 as c_v2, v3 as c_v3
from .one_to_many import v1 as m_v1, v2 as m_v2, v3 as m_v3, v4 as m_v4
from .one_to_one import v1 as o_v1, v3 as o_v3, v4 as o_v4, v5 as o_v5
from .pipeline import prompts as p_prompts

_ONE_TO_ONE: dict[str, str] = {
    "v1": o_v1.MATCH_PROMPT,
    "v3": o_v3.MATCH_PROMPT,
    "v4": o_v4.MATCH_PROMPT,
    "v5": o_v5.MATCH_PROMPT,
}

_ONE_TO_MANY: dict[str, str] = {
    "v1": m_v1.MATCH_PROMPT,
    "v2": m_v2.MATCH_PROMPT,
    "v3": m_v3.MATCH_PROMPT,
    "v4": m_v4.MATCH_PROMPT,
}

_PIPELINE: dict[str, str] = {
    "analyze_proposal": p_prompts.ANALYZE_PROPOSAL,
    "classify_candidates": p_prompts.CLASSIFY_CANDIDATES,
    "score_candidate": p_prompts.SCORE_CANDIDATE,
}

_CRITIC: dict[str, str] = {
    "v1": c_v1.CRITIC_PROMPT,
    "v2": c_v2.CRITIC_PROMPT,
    "v3": c_v3.CRITIC_PROMPT,
}


def get_prompt(
    version: str,
    one_to_many: bool = False,
    pipeline_step: str | None = None,
    critic_version: str | None = None,
) -> str:
    if critic_version is not None:
        if critic_version not in _CRITIC:
            available = list(_CRITIC)
            msg = f"Unknown critic prompt version {critic_version!r}. Available: {available}"
            raise ValueError(msg)
        return _CRITIC[critic_version]

    if pipeline_step:
        if pipeline_step not in _PIPELINE:
            available = list(_PIPELINE)
            raise ValueError(f"Unknown pipeline step {pipeline_step!r}. Available: {available}")
        return _PIPELINE[pipeline_step]

    registry = _ONE_TO_MANY if one_to_many else _ONE_TO_ONE
    if version not in registry:
        available = list(registry.keys())
        label = "one_to_many" if one_to_many else "one_to_one"
        raise ValueError(f"Unknown {label} prompt version {version!r}. Available: {available}")
    return registry[version]
