from agent_routing_eval_lab.evaluation.confidence import (
    MetricInterval,
    bootstrap_metric_intervals,
    intervals_overlap,
)
from agent_routing_eval_lab.evaluation.metrics import compute_policy_metrics


def _rows(n: int):
    rows = []
    for i in range(n):
        success = i % 2 == 0
        rows.append(
            {
                "candidate_tool": "a" if success else "b",
                "oracle_tool": "a",
                "success": success,
                "cost": 0.1,
                "latency_ms": 100,
                "unsafe_action": False,
                "requires_approval": False,
                "resolved": success,
                "utility_candidate": 0.5,
                "utility_oracle": 0.9,
                "support_count": 10,
            }
        )
    return rows


def test_bootstrap_intervals_bracket_point_and_are_deterministic() -> None:
    rows = _rows(80)
    point = compute_policy_metrics(rows)

    first = bootstrap_metric_intervals(rows, point, iterations=200, seed=7)
    second = bootstrap_metric_intervals(rows, point, iterations=200, seed=7)

    # Deterministic for a fixed seed.
    assert first.to_dict() == second.to_dict()

    score_ci = first.intervals["score"]
    assert score_ci.low <= score_ci.point <= score_ci.high
    success_ci = first.intervals["success_rate"]
    assert success_ci.low <= success_ci.point <= success_ci.high


def test_intervals_overlap_detects_clear_vs_overlapping() -> None:
    clear_a = MetricInterval(point=80.0, low=78.0, high=82.0)
    clear_b = MetricInterval(point=70.0, low=68.0, high=72.0)
    assert intervals_overlap(clear_a, clear_b) is False

    overlap_a = MetricInterval(point=80.0, low=75.0, high=85.0)
    overlap_b = MetricInterval(point=78.0, low=74.0, high=82.0)
    assert intervals_overlap(overlap_a, overlap_b) is True
