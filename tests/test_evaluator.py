from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter


def test_evaluator_returns_policy_summaries_and_warnings() -> None:
    records = [record.to_dict() for record in generate_synthetic_logs(rows=80, seed=4)]
    evaluator = OfflineEvaluator(records, support_threshold=8)
    results = evaluator.evaluate_many({"baseline": BaselineRouter(), "contextweaver_v1": ContextWeaverRouter()})

    assert len(results) == 2
    assert all(result.metrics.score >= 0 for result in results)
    assert all(result.metrics.support_coverage_warning for result in results)
