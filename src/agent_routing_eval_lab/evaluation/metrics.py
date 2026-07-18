from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from statistics import mean

from agent_routing_eval_lab.data.schemas import TOOL_CATALOG

# Fixed, dataset- and policy-independent normalizers derived from the global tool
# catalog. Using each policy's own max cost/latency made composite scores
# incomparable across policies (a policy that only picks cheap tools was
# penalized against its own cheap ceiling). Catalog-wide bounds keep the score
# comparable across policies and across evaluation runs.
_MAX_TOOL_COST = max((spec.avg_cost for spec in TOOL_CATALOG.values()), default=1.0) or 1.0
_MAX_TOOL_LATENCY_MS = max((spec.avg_latency_ms for spec in TOOL_CATALOG.values()), default=1.0) or 1.0

# Share of low-support decisions above which the offline estimate is flagged as
# under-supported. Exposed as the structured ``PolicyMetrics.low_support`` flag so
# consumers test the boolean instead of substring-matching the warning text.
LOW_SUPPORT_WARN_SHARE = 0.15


@dataclass(frozen=True)
class ScoreWeights:
    """Weights of the composite ``score`` (see docs/evaluation_methodology.md).

    The composite is a business-tunable weighted average — a refund agent weights
    safety far higher than a docs-search agent — so the weights are data here, not
    magic numbers baked into the formula. Each component is in [0, 1] (quality and
    "1 - badness" terms), the weights are scaled by 100, and by default they sum to
    1.0 so the score lands on a 0-100 scale.

    Defaults and rationale:

    - ``success`` (0.40): resolving the user's request correctly is the primary
      goal, so it carries the most weight.
    - ``correct_tool`` (0.20): picking the oracle tool is the routing quality
      signal, weighted below end-to-end success.
    - ``safety`` (0.15): ``1 - unsafe_action_rate``. A soft score term; hard safety
      vetoes live in the rollout recommendation (report), not here.
    - ``unresolved`` (0.10): ``1 - unresolved_request_rate``, penalizing requests
      left hanging even when no wrong action was taken.
    - ``cost`` / ``latency`` (0.075 each): efficiency terms on catalog-normalized
      cost and latency, deliberately the smallest weights.
    """

    success: float = 0.40
    correct_tool: float = 0.20
    safety: float = 0.15
    unresolved: float = 0.10
    cost: float = 0.075
    latency: float = 0.075

    def to_dict(self) -> dict[str, float]:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @classmethod
    def from_json(cls, path: Path) -> ScoreWeights:
        """Load weights from a JSON object file; unknown keys and negative weights are rejected."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"weights config {path} is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"weights config {path} must be a JSON object, got {type(raw).__name__}")
        allowed = {field.name for field in fields(cls)}
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError(f"weights config {path} has unknown key(s): {', '.join(sorted(unknown))}")
        coerced: dict[str, float] = {}
        for key, value in raw.items():
            try:
                coerced[key] = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"weights config {path}: '{key}' must be a number, got {value!r}") from exc
        # Every component is a "higher is better" term (quality and "1 - badness"),
        # so a negative weight would reward the wrong thing and silently distort the
        # composite score. Reject it loudly. Weights need not sum to 1.0: a partial
        # override keeps the other defaults, so the sum is intentionally not fixed.
        negative = sorted(key for key, value in coerced.items() if value < 0)
        if negative:
            raise ValueError(f"weights config {path}: weight(s) must be non-negative: {', '.join(negative)}")
        return cls(**coerced)


DEFAULT_WEIGHTS = ScoreWeights()


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
    low_support_share: float
    low_support: bool
    score: float


def _ratio(values: list[bool]) -> float:
    return mean(float(value) for value in values) if values else 0.0


def compute_policy_metrics(
    rows: list[dict], support_threshold: int = 5, *, weights: ScoreWeights = DEFAULT_WEIGHTS
) -> PolicyMetrics:
    if not rows:
        return PolicyMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "No rows provided.", 0.0, False, 0.0)

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
    low_support_flag = low_support_ratio > LOW_SUPPORT_WARN_SHARE
    coverage_warning = (
        f"{low_support_ratio:.1%} of decisions have low support (<{support_threshold} historical matches)."
        if low_support_flag
        else "Support coverage looks sufficient for this candidate policy."
    )

    normalized_cost = min(avg_cost / _MAX_TOOL_COST, 1.0)
    normalized_latency = min(avg_latency / _MAX_TOOL_LATENCY_MS, 1.0)

    score = 100 * (
        weights.success * success_rate
        + weights.correct_tool * correct_tool_rate
        + weights.safety * (1 - unsafe_rate)
        + weights.unresolved * (1 - unresolved_rate)
        + weights.cost * (1 - normalized_cost)
        + weights.latency * (1 - normalized_latency)
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
        low_support_share=low_support_ratio,
        low_support=low_support_flag,
        score=round(score, 3),
    )
