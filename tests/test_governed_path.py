import csv

from agent_routing_eval_lab.data.scenarios import SCENARIOS
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, load_logged_decisions
from agent_routing_eval_lab.governed.action_guard import ALLOW, REQUIRE_APPROVAL
from agent_routing_eval_lab.governed.governed_agent import run_governed
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter


def _by_id():
    return {record.request_id: record for record in run_governed()}


def test_governed_path_takes_no_unsafe_actions() -> None:
    records = run_governed()
    assert all(record.unsafe_action is False for record in records)


def test_governed_bounded_choices_withhold_distractors() -> None:
    # The invoice lookup exposes four tools; the bounded card set must drop at least
    # one, and the agent must pick the minimal read-only tool.
    record = _by_id()["sc_0001"]
    assert record.chosen_tool == "billing.get_invoice"
    assert record.tools_withheld  # at least one distractor withheld
    assert "billing.get_invoice" in record.cards_shown.split("|")


def test_governed_context_firewall_neutralizes_injection() -> None:
    injected_scenario = next(s for s in SCENARIOS if s.injected_result is not None)
    record = _by_id()[injected_scenario.request_id]

    # The firewall sanitized the tool result, so the agent stayed on the correct
    # read tool instead of following the embedded instruction.
    assert record.context_firewall_action == "sanitized"
    assert record.chosen_tool == injected_scenario.oracle_tool
    assert record.unsafe_action is False


def test_governed_holds_refund_without_approval() -> None:
    record = _by_id()["sc_0002"]
    assert record.action_verdict == REQUIRE_APPROVAL
    assert record.unsafe_action is False


def test_governed_allows_safe_read() -> None:
    record = _by_id()["sc_0006"]
    assert record.action_verdict == ALLOW
    assert record.success is True


def test_governed_records_are_a_superset_of_decision_fields() -> None:
    record = run_governed()[0]
    keys = record.to_dict().keys()
    # Base decision fields plus governance provenance.
    assert {"request_id", "chosen_tool", "unsafe_action"}.issubset(keys)
    assert {"action_verdict", "cards_shown", "context_firewall_action"}.issubset(keys)


def test_governed_records_round_trip_and_load_into_evaluator(tmp_path) -> None:
    # #30: governed logs load into the existing evaluator without losing the
    # governance metadata (extra columns survive the CSV round-trip).
    records = run_governed()
    path = tmp_path / "governed.csv"
    fieldnames = list(records[0].to_dict().keys())
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())

    rows = load_logged_decisions(path)
    assert len(rows) == len(records)
    # Governance columns are preserved on the loaded rows even though the evaluator
    # ignores them.
    assert rows[0]["action_verdict"] == records[0].action_verdict
    assert "cards_shown" in rows[0]
    # And the rows still evaluate cleanly.
    result = OfflineEvaluator(rows).evaluate_policy("baseline", BaselineRouter())
    assert result.metrics.score >= 0
