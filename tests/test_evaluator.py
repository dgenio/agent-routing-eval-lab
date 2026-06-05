import pytest

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
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
