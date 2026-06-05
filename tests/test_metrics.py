from agent_routing_eval_lab.evaluation.metrics import compute_policy_metrics


def test_compute_policy_metrics_basic() -> None:
    rows = [
        {
            "candidate_tool": "a",
            "oracle_tool": "a",
            "success": True,
            "cost": 0.1,
            "latency_ms": 100,
            "unsafe_action": False,
            "requires_approval": False,
            "resolved": True,
            "utility_candidate": 0.8,
            "utility_oracle": 0.9,
            "support_count": 10,
        },
        {
            "candidate_tool": "b",
            "oracle_tool": "a",
            "success": False,
            "cost": 0.2,
            "latency_ms": 200,
            "unsafe_action": True,
            "requires_approval": True,
            "resolved": False,
            "utility_candidate": -0.2,
            "utility_oracle": 0.7,
            "support_count": 1,
        },
    ]

    metrics = compute_policy_metrics(rows, support_threshold=5)
    assert metrics.success_rate == 0.5
    assert metrics.correct_tool_selection_rate == 0.5
    assert metrics.unsafe_action_rate == 0.5
    assert metrics.unresolved_request_rate == 0.5
    assert metrics.estimated_regret_vs_oracle > 0
    assert "low support" in metrics.support_coverage_warning.lower()
