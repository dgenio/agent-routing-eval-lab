import csv

from agent_routing_eval_lab.baseline.unsafe_agent import describe_run, run_unsafe_baseline
from agent_routing_eval_lab.data.scenarios import SCENARIOS
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, load_logged_decisions
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter


def test_unsafe_baseline_produces_at_least_three_distinct_failures() -> None:
    records = run_unsafe_baseline()
    failure_types = {record.failure_type for record in records if record.failure_type}
    assert len(failure_types) >= 3


def test_unsafe_baseline_is_steered_by_injection_payload() -> None:
    records = {record.request_id: record for record in run_unsafe_baseline()}
    injected_scenario = next(s for s in SCENARIOS if s.injected_result is not None)
    record = records[injected_scenario.request_id]

    # The baseline followed the embedded instruction and escalated to the target tool.
    assert record.chosen_tool == injected_scenario.injection_target
    assert record.failure_type == "context_pollution"
    assert record.unsafe_action is True


def test_unsafe_baseline_is_distracted_by_full_catalog() -> None:
    # The invoice lookup exposes irreversible billing writes; the ungoverned agent
    # reaches for one instead of the read-only invoice tool.
    record = {r.request_id: r for r in run_unsafe_baseline()}["sc_0001"]
    assert record.oracle_tool == "billing.get_invoice"
    assert record.chosen_tool != "billing.get_invoice"
    assert record.unsafe_action is True


def test_unsafe_baseline_logs_are_evaluator_ready(tmp_path) -> None:
    records = run_unsafe_baseline()
    path = tmp_path / "unsafe.csv"
    fieldnames = list(records[0].to_dict().keys())
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())

    rows = load_logged_decisions(path)
    result = OfflineEvaluator(rows).evaluate_policy("baseline", BaselineRouter())
    assert len(rows) == len(records)
    assert result.metrics.score >= 0


def test_describe_run_has_one_line_per_decision() -> None:
    records = run_unsafe_baseline()
    assert len(describe_run(records)) == len(records)
