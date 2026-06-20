import json

import pytest

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult
from agent_routing_eval_lab.evaluation.gates import GatePolicy, apply_gates, load_gate_policy
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics


def _result(name: str, *, success_rate: float, unsafe_rate: float, low_support: float, avg_cost: float):
    metrics = PolicyMetrics(
        success_rate=success_rate,
        correct_tool_selection_rate=success_rate,
        average_cost=avg_cost,
        average_latency_ms=100.0,
        unsafe_action_rate=unsafe_rate,
        approval_required_action_rate=0.0,
        unresolved_request_rate=0.0,
        estimated_regret_vs_oracle=0.0,
        support_coverage_warning="",
        low_support_share=low_support,
        score=0.0,
    )
    return PolicyEvaluationResult(policy_name=name, metrics=metrics, warnings=[])


def test_apply_gates_passes_when_within_thresholds() -> None:
    results = [_result("good", success_rate=0.95, unsafe_rate=0.0, low_support=0.05, avg_cost=0.1)]
    policy = GatePolicy(max_unsafe_rate=0.01, min_success_rate=0.9, max_low_support_share=0.2, max_avg_cost=0.5)
    assert apply_gates(results, policy) == []


def test_has_active_thresholds_distinguishes_empty_from_configured() -> None:
    assert not GatePolicy().has_active_thresholds()
    assert not GatePolicy(policy_name="only-a-target").has_active_thresholds()
    assert GatePolicy(max_unsafe_rate=0.05).has_active_thresholds()
    assert GatePolicy(min_success_rate=0.9, policy_name="b").has_active_thresholds()


def test_apply_gates_reports_each_violation() -> None:
    results = [_result("bad", success_rate=0.5, unsafe_rate=0.2, low_support=0.4, avg_cost=0.9)]
    policy = GatePolicy(max_unsafe_rate=0.01, min_success_rate=0.9, max_low_support_share=0.2, max_avg_cost=0.5)
    violations = apply_gates(results, policy)
    metrics_hit = {v.metric for v in violations}
    assert metrics_hit == {"unsafe_action_rate", "success_rate", "low_support_share", "average_cost"}


def test_apply_gates_can_target_a_single_policy() -> None:
    results = [
        _result("a", success_rate=0.5, unsafe_rate=0.0, low_support=0.0, avg_cost=0.1),
        _result("b", success_rate=0.99, unsafe_rate=0.0, low_support=0.0, avg_cost=0.1),
    ]
    policy = GatePolicy(min_success_rate=0.9, policy_name="b")
    assert apply_gates(results, policy) == []


def test_apply_gates_raises_for_unknown_target_policy() -> None:
    results = [_result("a", success_rate=0.99, unsafe_rate=0.0, low_support=0.0, avg_cost=0.1)]
    with pytest.raises(ValueError, match="was not evaluated"):
        apply_gates(results, GatePolicy(min_success_rate=0.9, policy_name="missing"))


def test_load_gate_policy_reads_json(tmp_path) -> None:
    path = tmp_path / "gate.json"
    path.write_text(json.dumps({"max_unsafe_rate": 0.01, "min_success_rate": 0.8}), encoding="utf-8")
    policy = load_gate_policy(path)
    assert policy.max_unsafe_rate == 0.01
    assert policy.min_success_rate == 0.8


def test_load_gate_policy_rejects_unknown_keys(tmp_path) -> None:
    path = tmp_path / "gate.json"
    path.write_text(json.dumps({"max_unsafe": 0.01}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown key"):
        load_gate_policy(path)


def test_load_gate_policy_rejects_malformed_json(tmp_path) -> None:
    path = tmp_path / "gate.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_gate_policy(path)
