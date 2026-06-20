from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult


@dataclass
class DecisionDiff:
    request_id: str
    intent: str
    tool_a: str
    tool_b: str
    success_a: bool
    success_b: bool
    unsafe_a: bool
    unsafe_b: bool
    cost_delta: float
    latency_delta: float

    @property
    def classification(self) -> str:
        """How policy B compares to policy A on this request.

        ``regression`` if B is worse on a safety/quality axis, ``improvement`` if
        better, otherwise ``neutral`` (tool changed but outcome did not).
        """
        if (self.unsafe_b and not self.unsafe_a) or (not self.success_b and self.success_a):
            return "regression"
        if (self.unsafe_a and not self.unsafe_b) or (self.success_b and not self.success_a):
            return "improvement"
        return "neutral"


@dataclass
class DiffResult:
    policy_a: str
    policy_b: str
    diffs: list[DecisionDiff]
    regressed: int
    improved: int
    neutral: int


def _index_by_request(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["request_id"]): row for row in rows}


def compute_decision_diffs(
    result_a: PolicyEvaluationResult,
    result_b: PolicyEvaluationResult,
) -> DiffResult:
    """Compute per-request differences between two evaluated policies.

    Only requests where the two policies chose a different tool are included.
    Requests are matched by ``request_id``; rows present for only one policy are
    skipped (the evaluators run on the same logs, so this is defensive).
    """
    rows_a = _index_by_request(result_a.scored_rows)
    rows_b = _index_by_request(result_b.scored_rows)

    diffs: list[DecisionDiff] = []
    for request_id in rows_a.keys() & rows_b.keys():
        row_a = rows_a[request_id]
        row_b = rows_b[request_id]
        if row_a["candidate_tool"] == row_b["candidate_tool"]:
            continue
        diffs.append(
            DecisionDiff(
                request_id=request_id,
                intent=str(row_a.get("intent", row_b.get("intent", ""))),
                tool_a=str(row_a["candidate_tool"]),
                tool_b=str(row_b["candidate_tool"]),
                success_a=bool(row_a["success"]),
                success_b=bool(row_b["success"]),
                unsafe_a=bool(row_a["unsafe_action"]),
                unsafe_b=bool(row_b["unsafe_action"]),
                cost_delta=float(row_b["cost"]) - float(row_a["cost"]),
                latency_delta=float(row_b["latency_ms"]) - float(row_a["latency_ms"]),
            )
        )

    # Stable, deterministic ordering: regressions first, then by request_id.
    order = {"regression": 0, "neutral": 1, "improvement": 2}
    diffs.sort(key=lambda d: (order[d.classification], d.request_id))

    regressed = sum(1 for d in diffs if d.classification == "regression")
    improved = sum(1 for d in diffs if d.classification == "improvement")
    neutral = sum(1 for d in diffs if d.classification == "neutral")
    return DiffResult(
        policy_a=result_a.policy_name,
        policy_b=result_b.policy_name,
        diffs=diffs,
        regressed=regressed,
        improved=improved,
        neutral=neutral,
    )
