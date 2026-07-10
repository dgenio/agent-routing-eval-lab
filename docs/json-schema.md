# JSON Results Schema

`evaluate --format json` and `report --json-output PATH` emit a stable,
machine-readable view of an evaluation run. This is the contract CI gates,
dashboards, and downstream scripts can rely on.

## Shape

```json
{
  "schema_version": "2",
  "input_path": "examples/logged_decisions.sample.csv",
  "row_count": 300,
  "winner": "contextweaver_v1",
  "ranking": ["contextweaver_v1", "baseline", "strict_policy", "cost_aware"],
  "policies": [
    {
      "policy_name": "contextweaver_v1",
      "metrics": {
        "success_rate": 0.7967,
        "correct_tool_selection_rate": 0.8367,
        "average_cost": 0.153,
        "average_latency_ms": 183.3,
        "unsafe_action_rate": 0.0267,
        "approval_required_action_rate": 0.2,
        "unresolved_request_rate": 0.0867,
        "estimated_regret_vs_oracle": 0.319,
        "support_coverage_warning": "…",
        "low_support_share": 0.12,
        "low_support": false,
        "score": 83.41
      },
      "off_policy": {
        "available": true,
        "ips": 0.71,
        "snips": 0.74,
        "n": 300,
        "matched": 214,
        "effective_sample_size": 118.4,
        "low_confidence": false,
        "reason": "sufficient overlap (match_rate=71.3%, ESS=118.4)"
      },
      "confidence": {
        "confidence": 0.95,
        "iterations": 500,
        "intervals": {
          "score": {"point": 83.41, "low": 81.9, "high": 84.8},
          "success_rate": {"point": 0.7967, "low": 0.75, "high": 0.84}
        }
      },
      "warnings": [
        {"code": "coverage.low_support", "severity": "warning", "message": "…"}
      ]
    }
  ]
}
```

## Fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version. Bumped only on breaking changes. |
| `input_path` | string \| null | The CSV the run read (null if not provided). |
| `row_count` | int \| null | Number of logged rows evaluated. |
| `winner` | string \| null | Highest-scoring policy (null when no policies). |
| `ranking` | string[] | Policy names ordered by descending score. |
| `policies` | object[] | One entry per policy, in ranking order. |
| `policies[].policy_name` | string | Policy identifier. |
| `policies[].metrics` | object | All fields of `PolicyMetrics` (see `evaluation/metrics.py`). These are oracle-anchored scenario-replay metrics. |
| `policies[].off_policy` | object \| null | IPS/SNIPS off-policy value estimate against the logged reward (see `evaluation/off_policy.py`). `available` is `false` — and `ips`/`snips` are `null` — when the logs carry no `propensity_score`/`reward`. `low_confidence` flags estimates resting on thin overlap with the logged actions. |
| `policies[].confidence` | object \| null | Seeded bootstrap confidence intervals: `{confidence, iterations, intervals}` where `intervals` maps each of `score`/`success_rate`/`unsafe_action_rate`/`average_cost`/`average_latency_ms` to `{point, low, high}`. `null` when interval computation was disabled. |
| `policies[].warnings` | object[] | Structured diagnostics: `{code, severity, message}`. `severity` is one of `info`, `warning`, `error`. |

Per-decision rows are intentionally **not** in this payload; use
`evaluate --dump-decisions DIR` for that (see [input-schema.md](input-schema.md)).

## Stability policy

The shape is versioned via `schema_version` (currently `"2"`):

- **Additive** changes (new keys) do **not** bump the version.
- **Renaming or removing** a key, or changing a value's type, is a breaking
  change and **must** bump `schema_version`.

Metric field names (`policies[].metrics.*`) are part of the public contract;
renaming one is a breaking change.
