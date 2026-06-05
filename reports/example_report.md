# Agent Routing Evaluation Report

Generated: 2026-06-05T05:35:15.188644+00:00

## Policy Comparison

| Policy | Success | Correct Tool | Avg Cost | Avg Latency (ms) | Unsafe | Unresolved | Regret | Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| contextweaver_v1 | 79.67% | 83.67% | $0.153 | 183.3 | 2.67% | 8.67% | 0.319 | 83.41 |
| baseline | 62.00% | 66.00% | $0.309 | 304.2 | 3.00% | 37.67% | 0.666 | 66.67 |
| strict_policy | 46.00% | 46.00% | $0.065 | 121.8 | 0.00% | 44.67% | 0.711 | 60.91 |
| cost_aware | 23.67% | 23.67% | $0.051 | 105.4 | 0.00% | 23.00% | 1.014 | 49.38 |

## Winner: `contextweaver_v1`

- Composite score: **83.41**
- Coverage check: 16.3% of decisions have low support (<5 historical matches).

## Warnings

- **contextweaver_v1**: 16.3% of decisions have low support (<5 historical matches).
- **contextweaver_v1**: skdr-eval not installed; using local adapter summary fallback.
- **baseline**: 34.0% of decisions have low support (<5 historical matches).
- **baseline**: skdr-eval not installed; using local adapter summary fallback.
- **strict_policy**: 54.0% of decisions have low support (<5 historical matches).
- **strict_policy**: skdr-eval not installed; using local adapter summary fallback.
- **cost_aware**: 75.3% of decisions have low support (<5 historical matches).
- **cost_aware**: skdr-eval not installed; using local adapter summary fallback.

## Notes

- This is offline replay on synthetic historical-style data.
- Use this report as a pre-rollout gate before online A/B tests.