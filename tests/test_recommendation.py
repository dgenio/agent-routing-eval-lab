from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics
from agent_routing_eval_lab.evaluation.recommendation import (
    CANARY,
    HOLD,
    REVISE,
    pareto_frontier,
    recommend_rollout,
)


def _metrics(*, success, unsafe, low_support_share, cost=0.1, latency=100.0) -> PolicyMetrics:
    return PolicyMetrics(
        success_rate=success,
        correct_tool_selection_rate=success,
        average_cost=cost,
        average_latency_ms=latency,
        unsafe_action_rate=unsafe,
        approval_required_action_rate=0.1,
        unresolved_request_rate=1 - success,
        estimated_regret_vs_oracle=0.1,
        support_coverage_warning="",
        low_support_share=low_support_share,
        low_support=low_support_share > 0.15,
        score=100 * success,
    )


def _result(name, metrics) -> PolicyEvaluationResult:
    return PolicyEvaluationResult(policy_name=name, metrics=metrics, warnings=[])


def test_unsafe_policy_is_held_regardless_of_score() -> None:
    # High success but unsafe over threshold => hold (safety veto), never canary.
    results = [_result("risky", _metrics(success=0.99, unsafe=0.10, low_support_share=0.0))]
    rec = recommend_rollout(results)["risky"]
    assert rec.verdict == HOLD
    assert "safety" in rec.reason


def test_low_support_policy_cannot_be_canary() -> None:
    results = [_result("thin", _metrics(success=0.9, unsafe=0.0, low_support_share=0.5))]
    rec = recommend_rollout(results)["thin"]
    assert rec.verdict == HOLD
    assert "coverage" in rec.reason


def test_low_quality_policy_is_revised() -> None:
    results = [_result("weak", _metrics(success=0.4, unsafe=0.0, low_support_share=0.0))]
    rec = recommend_rollout(results)["weak"]
    assert rec.verdict == REVISE


def test_clean_policy_is_canary() -> None:
    results = [_result("good", _metrics(success=0.85, unsafe=0.0, low_support_share=0.05))]
    rec = recommend_rollout(results)["good"]
    assert rec.verdict == CANARY


def test_pareto_frontier_excludes_dominated_policy() -> None:
    strong = _result("strong", _metrics(success=0.9, unsafe=0.0, low_support_share=0.0, cost=0.05, latency=50.0))
    weak = _result("weak", _metrics(success=0.5, unsafe=0.1, low_support_share=0.0, cost=0.5, latency=500.0))
    frontier = pareto_frontier([strong, weak])
    assert "strong" in frontier
    assert "weak" not in frontier
