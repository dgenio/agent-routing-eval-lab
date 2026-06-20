from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult

# Bump this whenever the JSON shape changes in a backward-incompatible way
# (renamed/removed fields). Additive fields do not require a bump. See
# docs/json-schema.md for the stability policy.
SCHEMA_VERSION = "1"


def results_to_dict(
    results: list[PolicyEvaluationResult],
    *,
    input_path: Path | str | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    """Serialize evaluation results into a stable, JSON-ready dictionary.

    The shape is a public contract documented in ``docs/json-schema.md`` and
    versioned via ``schema_version``. Per-decision ``scored_rows`` are deliberately
    excluded to keep the payload bounded; use ``--dump-decisions`` for those.
    """
    ranked = sorted(results, key=lambda item: item.metrics.score, reverse=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "input_path": str(input_path) if input_path is not None else None,
        "row_count": row_count,
        "winner": ranked[0].policy_name if ranked else None,
        "ranking": [result.policy_name for result in ranked],
        "policies": [
            {
                "policy_name": result.policy_name,
                "metrics": asdict(result.metrics),
                "warnings": list(result.warnings),
            }
            for result in ranked
        ],
    }


def results_to_json(
    results: list[PolicyEvaluationResult],
    *,
    input_path: Path | str | None = None,
    row_count: int | None = None,
    indent: int = 2,
) -> str:
    """Render :func:`results_to_dict` as a JSON string with a trailing newline."""
    payload = results_to_dict(results, input_path=input_path, row_count=row_count)
    return json.dumps(payload, indent=indent, sort_keys=True) + "\n"
