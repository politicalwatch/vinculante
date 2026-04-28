from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExpectedEntry:
    article: str
    proposal_refs: list[str]


@dataclass
class EvalCase:
    domain: str
    target_path: str
    proposals_path: str
    expected: list[ExpectedEntry]


def load_testset(path: Path) -> list[EvalCase]:
    data = json.loads(path.read_text())
    return [
        EvalCase(
            domain=c["domain"],
            target_path=c["target"],
            proposals_path=c["proposals"],
            expected=[ExpectedEntry(**e) for e in c["expected"]],
        )
        for c in data["cases"]
    ]
