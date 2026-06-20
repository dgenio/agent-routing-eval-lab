# Logged-Decisions Input Schema

The `evaluate`, `report`, `gate`, `compare`, and `validate` commands all read a
CSV of logged routing decisions. This page is the column-by-column contract for
that file. Run `agent-routing-eval-lab validate --input your.csv` to check a file
against it before evaluating.

## Columns

The loader requires the following columns. Order does not matter; extra columns
are ignored.

| Column | Type | Required | Allowed values | Used by evaluator | Notes |
|---|---|:---:|---|:---:|---|
| `request_id` | string | yes | any non-empty id | yes | Identifies each row in diffs, exports, and error messages. |
| `user_query` | string | yes | any | yes | The original request text passed to routers. |
| `intent` | string | yes | any | yes | Intent label; grouped for support/coverage. |
| `available_tools` | string | yes | `\|`-separated tool names | yes | Each name must exist in the tool catalog; at least one required. |
| `chosen_tool` | string | yes | a tool name | no\* | The tool the logging policy actually picked. |
| `oracle_tool` | string | yes | a catalog tool name | yes | The "correct" tool used to score candidates. |
| `success` | bool | yes | see booleans below | yes | Whether the logged decision succeeded. |
| `cost` | float | yes | `>= 0` | yes | Logged cost; rejected if negative or non-numeric. |
| `latency_ms` | int | yes | `>= 0` | yes | Logged latency in milliseconds. |
| `requires_approval` | bool | yes | see booleans below | yes | Whether the action needed approval. |
| `approval_granted` | bool | yes | see booleans below | yes | Whether approval was granted. |
| `unsafe_action` | bool | yes | see booleans below | yes | Whether the logged action was unsafe. |

\* `chosen_tool` is part of the logged record but the current evaluator scores
candidate policies against `oracle_tool`; it is retained for diffing and future
off-policy work.

The synthetic generator also emits `timestamp`, `tool_result`, `failure_type`,
`human_rating`, and `policy_version`. These are not required by the loader and
are ignored at evaluation time.

## Boolean parsing

Boolean columns are parsed strictly (case-insensitive, surrounding whitespace
trimmed):

- **True:** `1`, `true`, `yes`, `y`
- **False:** `0`, `false`, `no`, `n`, empty string

Any other value (e.g. `maybe`, `Y.`) is rejected with the offending value,
column, and `request_id` — it is never silently coerced to `False`.

## Tool catalog

`available_tools` and `oracle_tool` must reference tools defined in
`src/agent_routing_eval_lab/data/schemas.py::TOOL_CATALOG`. Unknown tool names
are reported as errors by `validate` and raise at evaluation time.

## Per-decision export

`evaluate --dump-decisions DIR` writes one `<policy>_decisions.csv` per policy
with these columns: `request_id`, `intent`, `candidate_tool`, `oracle_tool`,
`cost`, `latency_ms`, `requires_approval`, `unsafe_action`, `success`,
`resolved`, `support_count`, `utility_candidate`, `utility_oracle`.
