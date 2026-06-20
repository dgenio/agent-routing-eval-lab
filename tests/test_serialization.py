import dataclasses
import json

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics
from agent_routing_eval_lab.evaluation.serialization import SCHEMA_VERSION, results_to_dict, results_to_json
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter


def _results():
    records = [record.to_dict() for record in generate_synthetic_logs(rows=40, seed=2)]
    evaluator = OfflineEvaluator(records)
    return records, evaluator.evaluate_many({"baseline": BaselineRouter()})


def test_results_to_dict_includes_versioned_schema_and_all_metric_fields() -> None:
    records, results = _results()
    payload = results_to_dict(results, input_path="logs.csv", row_count=len(records))

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["row_count"] == len(records)
    assert payload["input_path"] == "logs.csv"
    assert payload["ranking"] == ["baseline"]
    assert payload["winner"] == "baseline"

    metric_keys = {field.name for field in dataclasses.fields(PolicyMetrics)}
    assert set(payload["policies"][0]["metrics"]) == metric_keys


def test_results_to_json_round_trips() -> None:
    _, results = _results()
    text = results_to_json(results)
    parsed = json.loads(text)
    assert parsed["policies"][0]["policy_name"] == "baseline"
    assert text.endswith("\n")


def test_results_to_dict_handles_empty_results() -> None:
    payload = results_to_dict([])
    assert payload["winner"] is None
    assert payload["ranking"] == []
    assert payload["policies"] == []
