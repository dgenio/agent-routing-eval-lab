from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult

# JSON keys accepted in a committed gate-policy config file. Kept in sync with the
# GatePolicy fields so a typo in the config is rejected rather than silently ignored.
_CONFIG_KEYS = {
    "max_unsafe_rate",
    "min_success_rate",
    "max_low_support_share",
    "max_avg_cost",
    "policy_name",
}


@dataclass
class GatePolicy:
    """Threshold set for the ``gate`` command. ``None`` disables a given check."""

    max_unsafe_rate: float | None = None
    min_success_rate: float | None = None
    max_low_support_share: float | None = None
    max_avg_cost: float | None = None
    # When set, only this policy is gated; otherwise every evaluated policy is gated.
    policy_name: str | None = None

    def has_active_thresholds(self) -> bool:
        """Whether any threshold check is configured.

        A gate with no thresholds can only ever pass, which silently defeats the
        command's purpose in CI — callers should reject that as a usage error
        rather than report a misleading "PASSED".
        """
        return any(
            threshold is not None
            for threshold in (
                self.max_unsafe_rate,
                self.min_success_rate,
                self.max_low_support_share,
                self.max_avg_cost,
            )
        )


@dataclass
class GateViolation:
    policy_name: str
    metric: str
    threshold: float
    actual: float

    def message(self) -> str:
        return (
            f"{self.policy_name}: {self.metric} = {self.actual:.4f} violates threshold {self.threshold:.4f}"
        )


def load_gate_policy(path: Path) -> GatePolicy:
    """Load a :class:`GatePolicy` from a committed JSON config file.

    Raises ``ValueError`` on malformed JSON or unknown keys so misconfigured gates
    fail loudly (exit code 2) rather than passing by accident.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"gate config {path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"gate config {path} must be a JSON object, got {type(raw).__name__}")
    unknown = set(raw) - _CONFIG_KEYS
    if unknown:
        raise ValueError(f"gate config {path} has unknown key(s): {', '.join(sorted(unknown))}")
    return GatePolicy(**raw)


def apply_gates(results: list[PolicyEvaluationResult], policy: GatePolicy) -> list[GateViolation]:
    """Return the list of threshold violations across the gated policies.

    An empty list means every gated policy passed.
    """
    violations: list[GateViolation] = []
    for result in results:
        if policy.policy_name is not None and result.policy_name != policy.policy_name:
            continue
        metrics = result.metrics
        if policy.max_unsafe_rate is not None and metrics.unsafe_action_rate > policy.max_unsafe_rate:
            violations.append(
                GateViolation(result.policy_name, "unsafe_action_rate", policy.max_unsafe_rate, metrics.unsafe_action_rate)
            )
        if policy.min_success_rate is not None and metrics.success_rate < policy.min_success_rate:
            violations.append(
                GateViolation(result.policy_name, "success_rate", policy.min_success_rate, metrics.success_rate)
            )
        if policy.max_low_support_share is not None and metrics.low_support_share > policy.max_low_support_share:
            violations.append(
                GateViolation(
                    result.policy_name, "low_support_share", policy.max_low_support_share, metrics.low_support_share
                )
            )
        if policy.max_avg_cost is not None and metrics.average_cost > policy.max_avg_cost:
            violations.append(
                GateViolation(result.policy_name, "average_cost", policy.max_avg_cost, metrics.average_cost)
            )

    if policy.policy_name is not None and not any(r.policy_name == policy.policy_name for r in results):
        raise ValueError(f"gate target policy '{policy.policy_name}' was not evaluated")
    return violations


def violations_to_dict(violations: list[GateViolation]) -> dict[str, Any]:
    """JSON-ready representation of gate results for ``--format json``."""
    return {
        "passed": not violations,
        "violations": [
            {
                "policy_name": v.policy_name,
                "metric": v.metric,
                "threshold": v.threshold,
                "actual": v.actual,
            }
            for v in violations
        ],
    }
