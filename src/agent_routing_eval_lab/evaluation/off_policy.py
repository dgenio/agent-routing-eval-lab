from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Honest off-policy value estimation for a deterministic candidate policy.
#
# The evaluator's other metrics are *oracle-anchored scenario replay*: they score
# a candidate's tool choice against the known ``oracle_tool`` and a catalog utility
# model. That answers "did the candidate pick the tool we labelled correct?" but it
# does not use the logged outcomes at all.
#
# This module answers a different, genuinely counterfactual question: "what average
# reward would this candidate policy have earned on the logged traffic?" — estimated
# only from the logged reward and the behavior policy's propensity, via inverse
# propensity scoring (IPS) and its self-normalized variant (SNIPS).
#
# Because the candidate routers are deterministic, the target policy assigns
# probability 1 to the single tool it would pick and 0 to every other. IPS then
# reduces to averaging ``reward / propensity`` over exactly the logged rows where
# the candidate reproduces the logged action, and 0 elsewhere. Rows the candidate
# would route differently contribute no signal — which is precisely why a candidate
# that rarely overlaps with the logs is extrapolating, and its estimate is flagged
# as low-confidence rather than reported as if certain.

# A candidate whose importance-weighted logged sample is this thin is extrapolating,
# not estimating; its IPS/SNIPS numbers are still reported but flagged low-confidence.
MIN_MATCH_RATE = 0.15
MIN_EFFECTIVE_SAMPLE_SIZE = 10.0


@dataclass(frozen=True)
class OffPolicyEstimate:
    """IPS/SNIPS off-policy value estimate for one candidate policy.

    ``available`` is ``False`` when the logs lack ``propensity_score``/``reward``,
    in which case only the oracle-anchored metrics are meaningful. ``low_confidence``
    marks estimates that rest on too little overlap with the logged actions.
    """

    available: bool
    ips: float | None
    snips: float | None
    n: int
    matched: int
    effective_sample_size: float
    low_confidence: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "ips": round(self.ips, 6) if self.ips is not None else None,
            "snips": round(self.snips, 6) if self.snips is not None else None,
            "n": self.n,
            "matched": self.matched,
            "effective_sample_size": round(self.effective_sample_size, 3) if self.available else None,
            "low_confidence": self.low_confidence,
            "reason": self.reason,
        }


def _has_logged_signal(row: dict[str, Any]) -> bool:
    """Whether a logged row carries both a propensity and a reward we can use."""
    if "propensity_score" not in row or "reward" not in row:
        return False
    return str(row.get("propensity_score", "")).strip() != "" and str(row.get("reward", "")).strip() != ""


def estimate_off_policy(
    logged_rows: list[dict[str, Any]],
    candidate_tools: list[str],
    *,
    min_match_rate: float = MIN_MATCH_RATE,
    min_effective_sample_size: float = MIN_EFFECTIVE_SAMPLE_SIZE,
) -> OffPolicyEstimate:
    """Estimate a deterministic candidate policy's value from logged rewards.

    ``candidate_tools[i]`` is the tool the candidate policy would route for
    ``logged_rows[i]``. Returns an unavailable estimate (never raises) when the
    logs do not carry the propensity/reward signal, so callers can fall back to
    oracle-anchored metrics with a clear diagnostic.
    """
    n = len(logged_rows)
    if n == 0:
        return OffPolicyEstimate(False, None, None, 0, 0, 0.0, True, "no logged rows to estimate from")
    if not all(_has_logged_signal(row) for row in logged_rows):
        return OffPolicyEstimate(
            False,
            None,
            None,
            n,
            0,
            0.0,
            True,
            "logs lack propensity_score/reward; off-policy estimate unavailable (oracle-anchored metrics only)",
        )

    weights: list[float] = []
    weighted_rewards: list[float] = []
    for row, candidate in zip(logged_rows, candidate_tools, strict=True):
        if candidate != row["chosen_tool"]:
            # Deterministic target policy assigns the logged action probability 0.
            continue
        propensity = float(row["propensity_score"])
        if propensity <= 0.0:
            continue
        weight = 1.0 / propensity
        weights.append(weight)
        weighted_rewards.append(weight * float(row["reward"]))

    matched = len(weights)
    if matched == 0:
        return OffPolicyEstimate(
            True,
            0.0,
            None,
            n,
            0,
            0.0,
            True,
            "candidate never reproduced a logged action; IPS=0 rests on no support",
        )

    sum_w = sum(weights)
    sum_wr = sum(weighted_rewards)
    ips = sum_wr / n
    snips = sum_wr / sum_w
    effective_sample_size = (sum_w * sum_w) / sum(w * w for w in weights)
    match_rate = matched / n
    low_confidence = match_rate < min_match_rate or effective_sample_size < min_effective_sample_size
    if low_confidence:
        reason = (
            f"thin overlap with logged actions (match_rate={match_rate:.1%}, "
            f"ESS={effective_sample_size:.1f}); estimate is high-variance extrapolation"
        )
    else:
        reason = f"sufficient overlap (match_rate={match_rate:.1%}, ESS={effective_sample_size:.1f})"
    return OffPolicyEstimate(True, ips, snips, n, matched, effective_sample_size, low_confidence, reason)
