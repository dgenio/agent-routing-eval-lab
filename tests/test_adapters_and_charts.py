from agent_routing_eval_lab.adapters.skdr_eval_adapter import SkdrEvalAdapter
from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.visualization.charts import ascii_score_chart
from agent_routing_eval_lab.warnings import WarningCode


def test_skdr_adapter_falls_back_without_native_and_warns() -> None:
    adapter = SkdrEvalAdapter()
    rows = [{"success": True, "cost": 0.1, "latency_ms": 100}]
    result = adapter.summarize(rows)

    # Never silently claims a native run.
    assert result.used_native_skdr is False
    # Emits an explicit, honest fallback diagnostic.
    assert result.warnings
    assert result.warnings[0].code in {WarningCode.SKDR_MISSING, WarningCode.SKDR_PENDING}
    assert result.summary["success_rate"] == 1.0


def test_skdr_adapter_handles_empty_rows() -> None:
    result = SkdrEvalAdapter().summarize([])
    assert result.summary["success_rate"] == 0.0
    assert result.used_native_skdr is False


def test_ascii_score_chart_renders_each_policy() -> None:
    logs = [record.to_dict() for record in generate_synthetic_logs(rows=60, seed=8)]
    results = OfflineEvaluator(logs, compute_confidence=False).evaluate_many({"baseline": BaselineRouter()})
    chart = ascii_score_chart(results)
    assert "baseline" in chart
    # A bar is drawn.
    assert "█" in chart


def test_ascii_score_chart_handles_empty_results() -> None:
    # Should not raise on an empty result set.
    chart = ascii_score_chart([])
    assert isinstance(chart, str)
