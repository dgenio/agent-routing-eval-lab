import pytest

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.evaluation.serialization import results_to_dict
from agent_routing_eval_lab.warnings import EvalWarning
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter


def test_eval_warning_str_returns_message() -> None:
    warning = EvalWarning(code="coverage.low_support", severity="warning", message="too sparse")
    assert str(warning) == "too sparse"
    assert warning.to_dict() == {
        "code": "coverage.low_support",
        "severity": "warning",
        "message": "too sparse",
    }


def test_eval_warning_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError, match="unknown severity"):
        EvalWarning(code="x", severity="catastrophic", message="m")


def test_low_support_drives_structured_warning_not_substring() -> None:
    # support_threshold high enough that most decisions are "low support".
    records = [record.to_dict() for record in generate_synthetic_logs(rows=60, seed=3)]
    evaluator = OfflineEvaluator(records, support_threshold=999)
    result = evaluator.evaluate_policy("baseline", BaselineRouter())

    assert result.metrics.low_support is True
    codes = {w.code for w in result.warnings}
    assert "coverage.low_support" in codes
    assert all(isinstance(w, EvalWarning) for w in result.warnings)


def test_serialized_warnings_are_structured_objects() -> None:
    records = [record.to_dict() for record in generate_synthetic_logs(rows=60, seed=3)]
    evaluator = OfflineEvaluator(records, support_threshold=999)
    results = evaluator.evaluate_many({"baseline": BaselineRouter()})

    payload = results_to_dict(results)
    warnings = payload["policies"][0]["warnings"]
    assert warnings, "expected at least one warning for an under-supported run"
    for warning in warnings:
        assert set(warning) == {"code", "severity", "message"}
        assert warning["severity"] in {"info", "warning", "error"}
