"""Seeded bootstrap confidence intervals for policy metrics (#115).

A single point estimate ("policy A scores 77.1") hides whether A is meaningfully
better than B or just noise on a small log. This resamples the scored decisions
with replacement, recomputes the headline metrics on each resample, and reports a
percentile interval — using only the standard library and a fixed seed, so the
intervals are deterministic and reproducible across runs.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from agent_routing_eval_lab.evaluation.metrics import DEFAULT_WEIGHTS, PolicyMetrics, ScoreWeights, compute_policy_metrics

DEFAULT_ITERATIONS = 500
DEFAULT_SEED = 1234
DEFAULT_CONFIDENCE = 0.95

# Metrics we bootstrap: attribute name on PolicyMetrics -> friendly label.
_BOOTSTRAP_METRICS = ("score", "success_rate", "unsafe_action_rate", "average_cost", "average_latency_ms")


@dataclass(frozen=True)
class MetricInterval:
    point: float
    low: float
    high: float

    def to_dict(self) -> dict[str, float]:
        return {"point": round(self.point, 4), "low": round(self.low, 4), "high": round(self.high, 4)}


@dataclass(frozen=True)
class ConfidenceIntervals:
    confidence: float
    iterations: int
    intervals: dict[str, MetricInterval]

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "iterations": self.iterations,
            "intervals": {name: interval.to_dict() for name, interval in self.intervals.items()},
        }


def _percentile(sorted_values: list[float], quantile: float) -> float:
    """Linear-interpolated percentile of an already-sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = quantile * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def bootstrap_metric_intervals(
    scored_rows: list[dict[str, Any]],
    point_metrics: PolicyMetrics,
    *,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    support_threshold: int = 5,
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    confidence: float = DEFAULT_CONFIDENCE,
) -> ConfidenceIntervals:
    """Percentile bootstrap intervals for the headline metrics of one policy.

    ``point_metrics`` supplies the full-sample point estimate; the interval bounds
    come from ``iterations`` resamples. Deterministic for a fixed ``seed``.
    """
    n = len(scored_rows)
    samples: dict[str, list[float]] = {name: [] for name in _BOOTSTRAP_METRICS}
    if n > 0:
        rng = random.Random(seed)
        for _ in range(iterations):
            resample = [scored_rows[rng.randrange(n)] for _ in range(n)]
            metrics = compute_policy_metrics(resample, support_threshold, weights=weights)
            for name in _BOOTSTRAP_METRICS:
                samples[name].append(getattr(metrics, name))

    lower_q = (1.0 - confidence) / 2.0
    upper_q = 1.0 - lower_q
    intervals: dict[str, MetricInterval] = {}
    for name in _BOOTSTRAP_METRICS:
        ordered = sorted(samples[name])
        intervals[name] = MetricInterval(
            point=getattr(point_metrics, name),
            low=_percentile(ordered, lower_q),
            high=_percentile(ordered, upper_q),
        )
    return ConfidenceIntervals(confidence=confidence, iterations=iterations, intervals=intervals)


def intervals_overlap(a: MetricInterval, b: MetricInterval) -> bool:
    """Whether two intervals overlap (used to judge whether a winner gap is clear)."""
    return a.low <= b.high and b.low <= a.high
