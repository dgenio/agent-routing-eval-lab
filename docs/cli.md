# CLI Reference

Every command is available two ways:

```bash
agent-routing-eval-lab <subcommand> [flags]      # installed console script
python -m agent_routing_eval_lab.cli <subcommand> [flags]
```

Each subcommand also accepts `-h`/`--help` for inline usage.

## Global flags

These apply to every subcommand and must be placed **before** the subcommand:

| Flag | Description |
|---|---|
| `--version` | Print the package version and exit. |
| `-v`, `--verbose` | Show all diagnostics (full warning lists, debug info) on stderr. |
| `-q`, `--quiet` | Suppress warning diagnostics. |

Diagnostics (warnings, progress) go to **stderr**; result data goes to **stdout**, so JSON output stays machine-consumable when piped.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, or `gate`/`validate` passed. |
| `1` | A `gate` threshold was violated, or `validate` found problems. The run worked; the result is "no-go". |
| `2` | Usage or data error: bad input, missing file, unknown policy, malformed gate config. |

Unexpected errors (genuine bugs) still surface a Python traceback.

## `generate-data`

Generate a synthetic logged-decisions CSV.

| Flag | Default | Description |
|---|---|---|
| `--output` | required | Destination CSV path. |
| `--rows` | `300` | Number of rows (must be a positive integer). |
| `--seed` | `7` | Random seed for deterministic output. |

```bash
agent-routing-eval-lab generate-data --output examples/logged_decisions.sample.csv --rows 300 --seed 7
```

## `evaluate`

Evaluate the built-in candidate policies against logged decisions.

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Logged-decisions CSV (see [input-schema.md](input-schema.md)). |
| `--format` | `text` | `text` for the ASCII chart, `json` for machine-readable results (see [json-schema.md](json-schema.md)). |
| `--dump-decisions` | _off_ | Directory to write one `<policy>_decisions.csv` per policy for drill-down analysis. |

```bash
agent-routing-eval-lab evaluate --input examples/logged_decisions.sample.csv
agent-routing-eval-lab evaluate --input examples/logged_decisions.sample.csv --format json
agent-routing-eval-lab evaluate --input examples/logged_decisions.sample.csv --dump-decisions out/
```

## `report`

Write the Markdown evaluation report (optionally also JSON).

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Logged-decisions CSV. |
| `--output` | required | Markdown report path (written atomically). |
| `--json-output` | _off_ | Also write machine-readable JSON results to this path. |

```bash
agent-routing-eval-lab report --input examples/logged_decisions.sample.csv --output reports/example_report.md
```

## `demo`

Generate data, evaluate, and write a report end-to-end.

| Flag | Default | Description |
|---|---|---|
| `--output-dir` | current directory | Where to write `examples/` and `reports/` artifacts. Files are written atomically and resolved paths are printed. |

```bash
agent-routing-eval-lab demo
agent-routing-eval-lab demo --output-dir /tmp/demo-run
```

## `gate`

Evaluate policies and exit non-zero when thresholds are violated — the CI pre-deployment gate.

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Logged-decisions CSV. |
| `--max-unsafe-rate` | _off_ | Fail if any gated policy's unsafe-action rate exceeds this. |
| `--min-success-rate` | _off_ | Fail if success rate is below this. |
| `--max-low-support-share` | _off_ | Fail if the low-support share exceeds this. |
| `--max-avg-cost` | _off_ | Fail if average cost exceeds this. |
| `--policy-name` | all | Gate only this policy instead of every evaluated one. |
| `--config` | _off_ | Load thresholds from a committed JSON file (keys match the flags above plus `policy_name`). |
| `--format` | `text` | `text` or `json` violation output. |

```bash
agent-routing-eval-lab gate --input examples/logged_decisions.sample.csv --max-unsafe-rate 0.05 --min-success-rate 0.6
```

Use as a CI step:

```yaml
- name: Routing gate
  run: agent-routing-eval-lab gate --input logs.csv --max-unsafe-rate 0.05
```

## `compare`

Show request-level decision diffs between two policies (incumbent vs candidate).

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Logged-decisions CSV. |
| `--policy-a` | required | First policy name (the baseline/incumbent). |
| `--policy-b` | required | Second policy name (the candidate). |
| `--limit` | `20` | Maximum number of differing requests to show. |
| `--only-regressions` | _off_ | Show only requests where policy B regressed. |
| `--format` | `text` | `text` or `json`. |

Valid policy names: `baseline`, `cost_aware`, `strict_policy`, `contextweaver_v1`. An unknown name exits `2`.

```bash
agent-routing-eval-lab compare --input examples/logged_decisions.sample.csv --policy-a baseline --policy-b strict_policy --only-regressions
```

## `validate`

Check a bring-your-own logged-decisions CSV against the schema before evaluating.

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Logged-decisions CSV to validate. |
| `--max-errors` | all | Stop after reporting this many errors. |

Exits `0` when the file is valid, `1` (with errors on stderr) otherwise. See [input-schema.md](input-schema.md) for the column contract.

```bash
agent-routing-eval-lab validate --input my_logs.csv
```
