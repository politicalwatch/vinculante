from .v1 import (
    document_overview as _v1_doc_overview,
)
from .v1 import (
    gaps as _v1_gaps,
)
from .v1 import (
    highlights as _v1_highlights,
)
from .v1 import (
    synthesize as _v1_synthesize,
)
from .v1 import (
    themes as _v1_themes,
)

_NODES = ("document_overview", "themes", "highlights", "gaps", "synthesize")

_REGISTRY: dict[str, dict[str, str]] = {
    "v1": {
        "document_overview": _v1_doc_overview.PROMPT,
        "themes": _v1_themes.PROMPT,
        "highlights": _v1_highlights.PROMPT,
        "gaps": _v1_gaps.PROMPT,
        "synthesize": _v1_synthesize.PROMPT,
    }
}


def get_prompt(node: str, version: str = "v1") -> str:
    if version not in _REGISTRY:
        raise ValueError(
            f"Unknown summary prompt version {version!r}. Available: {list(_REGISTRY)}"
        )
    registry = _REGISTRY[version]
    if node not in registry:
        raise ValueError(f"Unknown summary prompt node {node!r}. Available: {list(registry)}")
    return registry[node]
