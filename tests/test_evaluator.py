import csv

import pytest

from agent_routing_eval_lab.adapters.skdr_eval_adapter import SkdrAdapterResult
from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation import evaluator as evaluator_module
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, load_logged_decisions
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter


class _FixedRouter:
    """Test router that always returns a preset tool."""

    def __init__(self, tool: str) -> None:
        self._tool = tool

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        return self._tool


def _row(**overrides: object) -> dict:
    row = {
        "request_id": "r1",
        "user_query": "q",
        "intent": "audit_export",
        "available_tools": "audit.export_case|docs.search_policy",
        "chosen_tool": "audit.export_case",
        "oracle_tool": "audit.export_case",
        "approval_granted": False,
    }
    row.update(overrides)
    return row


def test_evaluator_returns_policy_summaries_and_warnings() -> None:
    records = [record.to_dict() for record in generate_synthetic_logs(rows=80, seed=4)]
    evaluator = OfflineEvaluator(records, support_threshold=8)
    results = evaluator.evaluate_many({"baseline": BaselineRouter(), "contextweaver_v1": ContextWeaverRouter()})

    assert len(results) == 2
    assert all(result.metrics.score >= 0 for result in results)
    assert all(result.metrics.support_coverage_warning for result in results)


def test_evaluator_rejects_empty_available_tools() -> None:
    evaluator = OfflineEvaluator([_row(available_tools="")])
    with pytest.raises(ValueError, match="available_tools"):
        evaluator.evaluate_policy("p", _FixedRouter("docs.search_policy"))


def test_evaluator_rejects_unknown_tool() -> None:
    evaluator = OfflineEvaluator([_row(available_tools="not.a.real.tool")])
    with pytest.raises(ValueError, match="unknown tool"):
        evaluator.evaluate_policy("p", _FixedRouter("not.a.real.tool"))


def test_evaluator_rejects_unknown_oracle_tool() -> None:
    evaluator = OfflineEvaluator([_row(oracle_tool="not.a.real.tool")])
    with pytest.raises(ValueError, match="oracle_tool"):
        evaluator.evaluate_policy("p", _FixedRouter("docs.search_policy"))


def test_sensitive_tool_without_approval_is_unsafe() -> None:
    # audit.export_case requires approval; selecting it without approval must count as unsafe.
    evaluator = OfflineEvaluator([_row()])
    result = evaluator.evaluate_policy("p", _FixedRouter("audit.export_case"))
    assert result.metrics.unsafe_action_rate == 1.0


def test_load_logged_decisions_rejects_missing_required_columns(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    path.write_text("request_id,user_query\nr1,q\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required column"):
        load_logged_decisions(path)


def test_load_logged_decisions_rejects_invalid_boolean_values(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    row = generate_synthetic_logs(rows=1, seed=1)[0].to_dict()
    row["success"] = "maybe"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(ValueError, match="invalid boolean value"):
        load_logged_decisions(path)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("cost", "free", "invalid numeric value"),
        ("cost", "-0.1", "non-negative"),
        ("latency_ms", "slow", "invalid numeric value"),
        ("latency_ms", "-10", "non-negative"),
    ],
)
def test_load_logged_decisions_rejects_invalid_numeric_values(
    tmp_path, column: str, value: str, message: str
) -> None:
    path = tmp_path / "logs.csv"
    row = generate_synthetic_logs(rows=1, seed=1)[0].to_dict()
    row[column] = value

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(ValueError, match=message):
        load_logged_decisions(path)


class _RecordingRouter:
    """Router that records the metadata dict it is handed at decision time."""

    def __init__(self) -> None:
        self.seen_metadata: list[dict] = []

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        self.seen_metadata.append(dict(metadata or {}))
        return available_tools[0]


def test_routers_never_receive_oracle_tool_metadata() -> None:
    # Evaluation-leakage guard (#62): the ground-truth oracle_tool must not be
    # visible to a router, or any router could trivially return it.
    records = [record.to_dict() for record in generate_synthetic_logs(rows=25, seed=5)]
    router = _RecordingRouter()
    OfflineEvaluator(records).evaluate_policy("recording", router)

    assert router.seen_metadata, "router was never invoked"
    assert all("oracle_tool" not in meta for meta in router.seen_metadata)
    assert all("approval_granted" in meta for meta in router.seen_metadata)


def test_resolves_without_success_is_driven_by_tool_spec() -> None:
    # docs.search_policy has resolves_without_success=True, so a non-success
    # decision on it still counts as resolved (#64).
    row = _row(intent="policy_lookup", oracle_tool="crm.search_customer", available_tools="docs.search_policy|crm.search_customer")
    scored = OfflineEvaluator([row])._score_decision(row=row, candidate_tool="docs.search_policy")
    assert scored["success"] is False
    assert scored["resolved"] is True

    # crm.search_customer does not resolve-without-success: wrong tool -> unresolved.
    scored_other = OfflineEvaluator([row])._score_decision(row=row, candidate_tool="crm.search_customer")
    assert scored_other["success"] is True  # matches oracle here
    row2 = _row(intent="invoice_question", oracle_tool="billing.get_invoice", available_tools="crm.search_customer|billing.get_invoice")
    scored_wrong = OfflineEvaluator([row2])._score_decision(row=row2, candidate_tool="crm.search_customer")
    assert scored_wrong["success"] is False
    assert scored_wrong["resolved"] is False


def test_evaluator_uses_injected_adapter() -> None:
    # Adapter injection (#66): the evaluator must use the adapter it is given
    # instead of constructing its own.
    sentinel = evaluator_module.EvalWarning(code="test.injected", severity="info", message="injected adapter ran")

    class _FakeAdapter:
        def summarize(self, rows):
            return SkdrAdapterResult(summary={}, warnings=[sentinel], used_native_skdr=False)

    records = [record.to_dict() for record in generate_synthetic_logs(rows=20, seed=6)]
    evaluator = OfflineEvaluator(records, skdr_adapter=_FakeAdapter())
    result = evaluator.evaluate_policy("baseline", BaselineRouter())

    assert sentinel in result.warnings


def test_oracle_utility_uses_named_constants() -> None:
    # Utility-model constants (#67): oracle utility is reconstructable from the
    # named coefficients, and an oracle-matching safe decision has zero regret.
    from agent_routing_eval_lab.data.schemas import TOOL_CATALOG

    row = _row(
        intent="customer_lookup",
        oracle_tool="crm.search_customer",
        available_tools="crm.search_customer",
        approval_granted=True,
    )
    scored = OfflineEvaluator([row])._score_decision(row=row, candidate_tool="crm.search_customer")
    spec = TOOL_CATALOG["crm.search_customer"]
    expected_oracle = (
        evaluator_module.SUCCESS_REWARD
        - spec.avg_cost * evaluator_module.COST_WEIGHT
        - (spec.avg_latency_ms / 1000.0) * evaluator_module.LATENCY_WEIGHT_PER_SECOND
    )
    assert scored["utility_oracle"] == pytest.approx(expected_oracle)
    # Candidate == oracle, safe and successful -> identical utility, zero regret.
    assert scored["utility_candidate"] == pytest.approx(scored["utility_oracle"])
