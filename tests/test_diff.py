from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.diff import compute_decision_diffs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter


def _eval():
    records = [record.to_dict() for record in generate_synthetic_logs(rows=120, seed=5)]
    evaluator = OfflineEvaluator(records)
    results = evaluator.evaluate_many({"baseline": BaselineRouter(), "strict_policy": StrictPolicyRouter()})
    return {result.policy_name: result for result in results}


def test_diff_counts_partition_all_diffs() -> None:
    results = _eval()
    diff = compute_decision_diffs(results["baseline"], results["strict_policy"])

    # Every listed diff is a tool change, and the three classifications partition them.
    assert all(d.tool_a != d.tool_b for d in diff.diffs)
    assert diff.regressed + diff.improved + diff.neutral == len(diff.diffs)
    assert diff.regressed > 0  # strict_policy is known to regress vs baseline on this data


def test_diff_of_identical_policy_is_empty() -> None:
    results = _eval()
    diff = compute_decision_diffs(results["baseline"], results["baseline"])
    assert diff.diffs == []
    assert (diff.regressed, diff.improved, diff.neutral) == (0, 0, 0)


def test_diff_regressions_sort_first() -> None:
    results = _eval()
    diff = compute_decision_diffs(results["baseline"], results["strict_policy"])
    classifications = [d.classification for d in diff.diffs]
    # Regressions are grouped ahead of neutral/improvement entries.
    assert classifications == sorted(
        classifications, key={"regression": 0, "neutral": 1, "improvement": 2}.get
    )
