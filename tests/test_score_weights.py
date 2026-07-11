import pytest

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, rank_results
from agent_routing_eval_lab.evaluation.metrics import ScoreWeights, compute_policy_metrics
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.cost_aware_router import CostAwareRouter


def _rows():
    return [
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
        }
    ]


def test_score_is_reproducible_for_fixed_input() -> None:
    rows = _rows()
    first = compute_policy_metrics(rows).score
    second = compute_policy_metrics(rows).score
    assert first == second


def test_weights_from_json_round_trip_and_rejects_unknown_keys(tmp_path) -> None:
    good = tmp_path / "w.json"
    good.write_text('{"success": 0.5, "safety": 0.5}', encoding="utf-8")
    weights = ScoreWeights.from_json(good)
    assert weights.success == 0.5
    assert weights.safety == 0.5
    # Unspecified keys keep their defaults.
    assert weights.cost == ScoreWeights().cost

    bad = tmp_path / "bad.json"
    bad.write_text('{"speed": 1.0}', encoding="utf-8")
    with pytest.raises(ValueError, match="unknown key"):
        ScoreWeights.from_json(bad)

    non_numeric = tmp_path / "nonnum.json"
    non_numeric.write_text('{"success": "high"}', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a number"):
        ScoreWeights.from_json(non_numeric)


def test_reweighting_changes_ranking() -> None:
    # cost_aware picks cheap tools but resolves less; baseline resolves more but
    # costs more. A cost-only weighting should rank cost_aware above baseline,
    # while a success-only weighting should reverse that.
    records = [record.to_dict() for record in generate_synthetic_logs(rows=200, seed=3)]
    policies = {"baseline": BaselineRouter(), "cost_aware": CostAwareRouter()}

    cost_first = OfflineEvaluator(
        records, weights=ScoreWeights(success=0.0, correct_tool=0.0, safety=0.0, unresolved=0.0, cost=1.0, latency=0.0)
    ).evaluate_many(policies)
    success_first = OfflineEvaluator(
        records, weights=ScoreWeights(success=1.0, correct_tool=0.0, safety=0.0, unresolved=0.0, cost=0.0, latency=0.0)
    ).evaluate_many(policies)

    cost_winner = rank_results(cost_first)[0].policy_name
    success_winner = rank_results(success_first)[0].policy_name
    assert cost_winner == "cost_aware"
    assert success_winner == "baseline"
    assert cost_winner != success_winner
