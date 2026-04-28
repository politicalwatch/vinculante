from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from vinculante.application.evaluation.evaluator_service import EvaluationReport
from vinculante.infrastructure.config.settings import Settings


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(
    report: EvaluationReport,
    testset_path: Path,
    settings: Settings,
    out_dir: Path,
    min_degree: str = "bajo",
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=UTC)
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{report.domain}.json"

    payload = {
        "run_at": now.isoformat(),
        "testset_path": str(testset_path),
        "testset_sha256": _sha256(testset_path),
        "domain": report.domain,
        "target_id": report.target_id,
        "settings": {
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "llm_temperature": settings.llm_temperature,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "matching_top_k": settings.matching_top_k,
            "matching_confidence_threshold": settings.matching_confidence_threshold,
            "matching_strategy": settings.matching_strategy,
            "matching_prompt_version": settings.matching_prompt_version,
            "matching_critic_prompt_version": settings.matching_critic_prompt_version,
            "min_degree": min_degree,
        },
        "article_metrics": [asdict(m) for m in report.article_metrics],
        "aggregate": asdict(report.aggregate),
        "diagnostics": asdict(report.diagnostics),
        "matches": [asdict(m) for m in report.raw_matches],
    }

    out_path = out_dir / filename
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path
