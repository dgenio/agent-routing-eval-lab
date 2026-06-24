from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult, rank_results
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics


def _result(name: str, score: float) -> PolicyEvaluationResult:
    metrics = PolicyMetrics(
        success_rate=0.0,
        correct_tool_selection_rate=0.0,
        average_cost=0.0,
        average_latency_ms=0.0,
        unsafe_action_rate=0.0,
        approval_required_action_rate=0.0,
        unresolved_request_rate=0.0,
        estimated_regret_vs_oracle=0.0,
        support_coverage_warning="",
        low_support_share=0.0,
        low_support=False,
        score=score,
    )
    return PolicyEvaluationResult(policy_name=name, metrics=metrics, warnings=[])


def test_rank_results_orders_by_score_descending() -> None:
    ranked = rank_results([_result("a", 10.0), _result("b", 90.0), _result("c", 50.0)])
    assert [r.policy_name for r in ranked] == ["b", "c", "a"]


def test_rank_results_breaks_ties_by_policy_name() -> None:
    # Equal scores: order must be deterministic (name ascending), not dependent on
    # the order policies happened to be registered/evaluated.
    forward = rank_results([_result("zeta", 50.0), _result("alpha", 50.0)])
    reverse = rank_results([_result("alpha", 50.0), _result("zeta", 50.0)])
    assert [r.policy_name for r in forward] == ["alpha", "zeta"]
    assert [r.policy_name for r in reverse] == ["alpha", "zeta"]
