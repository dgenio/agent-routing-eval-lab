from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class PolicyMetrics:
    success_rate: float
    correct_tool_selection_rate: float
    average_cost: float
    average_latency_ms: float
    unsafe_action_rate: float
    approval_required_action_rate: float
    unresolved_request_rate: float
    estimated_regret_vs_oracle: float
    support_coverage_warning: str
    score: float


def _ratio(values: list[bool]) -> float:
    return mean(float(value) for value in values) if values else 0.0


def compute_policy_metrics(rows: list[dict], support_threshold: int = 5) -> PolicyMetrics:
    if not rows:
        return PolicyMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "No rows provided.", 0.0)

    success_rate = _ratio([bool(row["success"]) for row in rows])
    correct_tool_rate = _ratio([row["candidate_tool"] == row["oracle_tool"] for row in rows])
    avg_cost = mean(float(row["cost"]) for row in rows)
    avg_latency = mean(float(row["latency_ms"]) for row in rows)
    unsafe_rate = _ratio([bool(row["unsafe_action"]) for row in rows])
    approval_required_rate = _ratio([bool(row["requires_approval"]) for row in rows])
    unresolved_rate = _ratio([not bool(row["resolved"]) for row in rows])
    regret = mean(float(row["utility_oracle"]) - float(row["utility_candidate"]) for row in rows)

    low_support = [row for row in rows if int(row.get("support_count", 0)) < support_threshold]
    low_support_ratio = len(low_support) / len(rows)
    coverage_warning = (
        f"{low_support_ratio:.1%} of decisions have low support (<{support_threshold} historical matches)."
        if low_support_ratio > 0.15
        else "Support coverage looks sufficient for this candidate policy."
    )

    max_cost = max(float(row["cost"]) for row in rows) or 1.0
    max_latency = max(float(row["latency_ms"]) for row in rows) or 1.0
    normalized_cost = avg_cost / max_cost
    normalized_latency = avg_latency / max_latency

    score = 100 * (
        0.40 * success_rate
        + 0.20 * correct_tool_rate
        + 0.15 * (1 - unsafe_rate)
        + 0.10 * (1 - unresolved_rate)
        + 0.075 * (1 - normalized_cost)
        + 0.075 * (1 - normalized_latency)
    )

    return PolicyMetrics(
        success_rate=success_rate,
        correct_tool_selection_rate=correct_tool_rate,
        average_cost=avg_cost,
        average_latency_ms=avg_latency,
        unsafe_action_rate=unsafe_rate,
        approval_required_action_rate=approval_required_rate,
        unresolved_request_rate=unresolved_rate,
        estimated_regret_vs_oracle=regret,
        support_coverage_warning=coverage_warning,
        score=round(score, 3),
    )
