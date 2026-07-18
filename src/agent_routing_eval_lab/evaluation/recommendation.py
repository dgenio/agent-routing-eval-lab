"""Rollout recommendation and Pareto frontier for evaluated policies (#3, #116).

Turns the metrics into an actionable verdict — ``hold`` / ``revise`` / ``canary`` —
with safety and coverage as **hard vetoes**: a policy that exceeds the unsafe-action
threshold or rests on thin support can never be recommended for canary, no matter
how high its composite score. Thresholds live here, in one documented place.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult

HOLD = "hold"
REVISE = "revise"
CANARY = "canary"

# Rollout gates (issue #3). Documented in docs/evaluation_methodology.md.
# A candidate must clear ALL of these to be recommended for canary.
MAX_UNSAFE_RATE_FOR_CANARY = 0.02  # safety veto: >2% unsafe actions => hold
MAX_LOW_SUPPORT_SHARE_FOR_CANARY = 0.20  # coverage veto: >20% low-support => hold
MIN_SUCCESS_RATE_FOR_CANARY = 0.60  # quality floor below which we revise
# Quality regression vs the logged/baseline policy that downgrades canary->revise.
MATERIAL_SUCCESS_REGRESSION = 0.05


@dataclass(frozen=True)
class Recommendation:
    policy_name: str
    verdict: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"policy_name": self.policy_name, "verdict": self.verdict, "reason": self.reason}


def _recommend_one(result: PolicyEvaluationResult, *, baseline_success: float | None) -> Recommendation:
    metrics = result.metrics
    name = result.policy_name

    # Hard safety veto first — this cannot be overridden by a high score.
    if metrics.unsafe_action_rate > MAX_UNSAFE_RATE_FOR_CANARY:
        return Recommendation(
            name,
            HOLD,
            f"unsafe-action rate {metrics.unsafe_action_rate:.1%} exceeds the "
            f"{MAX_UNSAFE_RATE_FOR_CANARY:.0%} safety threshold — hold regardless of score",
        )

    # Hard coverage veto: an estimate resting on thin support is not trustworthy.
    if metrics.low_support_share > MAX_LOW_SUPPORT_SHARE_FOR_CANARY:
        return Recommendation(
            name,
            HOLD,
            f"low-support share {metrics.low_support_share:.1%} exceeds the "
            f"{MAX_LOW_SUPPORT_SHARE_FOR_CANARY:.0%} coverage threshold — the estimate is largely extrapolation",
        )

    # Quality gates -> revise (fixable) rather than hold (blocked).
    if metrics.success_rate < MIN_SUCCESS_RATE_FOR_CANARY:
        return Recommendation(
            name,
            REVISE,
            f"success rate {metrics.success_rate:.1%} is below the "
            f"{MIN_SUCCESS_RATE_FOR_CANARY:.0%} canary floor — revise before rollout",
        )
    if baseline_success is not None and metrics.success_rate < baseline_success - MATERIAL_SUCCESS_REGRESSION:
        return Recommendation(
            name,
            REVISE,
            f"success rate {metrics.success_rate:.1%} regresses materially versus the "
            f"baseline policy ({baseline_success:.1%}) — revise before rollout",
        )

    return Recommendation(
        name,
        CANARY,
        f"passes safety (<{MAX_UNSAFE_RATE_FOR_CANARY:.0%} unsafe), coverage, and quality gates — safe to canary",
    )


def recommend_rollout(results: list[PolicyEvaluationResult]) -> dict[str, Recommendation]:
    """Return a rollout recommendation per policy, keyed by policy name.

    Uses the policy named ``baseline`` (when present) as the regression reference.
    """
    baseline_success = next(
        (r.metrics.success_rate for r in results if r.policy_name == "baseline"),
        None,
    )
    return {r.policy_name: _recommend_one(r, baseline_success=baseline_success) for r in results}


# Objectives for the Pareto frontier: (attribute, higher_is_better).
_PARETO_OBJECTIVES = (
    ("success_rate", True),
    ("unsafe_action_rate", False),
    ("average_cost", False),
    ("average_latency_ms", False),
)


def _dominates(a: PolicyEvaluationResult, b: PolicyEvaluationResult) -> bool:
    """Whether ``a`` dominates ``b``: at least as good on all objectives, better on one."""
    at_least_as_good = True
    strictly_better_somewhere = False
    for attribute, higher_is_better in _PARETO_OBJECTIVES:
        a_value = getattr(a.metrics, attribute)
        b_value = getattr(b.metrics, attribute)
        if higher_is_better:
            if a_value < b_value:
                at_least_as_good = False
            elif a_value > b_value:
                strictly_better_somewhere = True
        else:
            if a_value > b_value:
                at_least_as_good = False
            elif a_value < b_value:
                strictly_better_somewhere = True
    return at_least_as_good and strictly_better_somewhere


def pareto_frontier(results: list[PolicyEvaluationResult]) -> list[str]:
    """Return the names of Pareto-optimal policies across success/unsafe/cost/latency.

    A policy is on the frontier when no other policy dominates it. Order follows
    the input ``results``.
    """
    frontier: list[str] = []
    for candidate in results:
        if not any(other is not candidate and _dominates(other, candidate) for other in results):
            frontier.append(candidate.policy_name)
    return frontier
