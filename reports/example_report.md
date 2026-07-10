# Agent Routing Evaluation Report

Generated: 2026-01-01T00:00:00+00:00

## Policy Comparison

Oracle-anchored scenario-replay metrics. Higher `Score` is better.

| Policy | Success | Correct Tool | Approval Req | Avg Cost | Avg Latency (ms) | Unsafe | Unresolved | Regret | Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| contextweaver_v1 | 71.00% | 71.00% | 25.33% | $0.162 | 193.7 | 0.33% | 19.67% | 0.408 | 76.42 |
| contextweaver_v2 | 71.00% | 71.00% | 25.33% | $0.162 | 193.7 | 0.33% | 19.67% | 0.408 | 76.42 |
| baseline | 65.33% | 69.33% | 46.00% | $0.313 | 306.5 | 4.33% | 34.00% | 0.620 | 68.77 |
| strict_policy | 44.33% | 44.33% | 11.33% | $0.081 | 132.7 | 0.00% | 45.00% | 0.729 | 59.57 |
| cost_aware | 22.67% | 22.67% | 11.33% | $0.069 | 118.3 | 0.00% | 21.67% | 1.024 | 49.21 |

## Winner: `contextweaver_v1`

- Composite score: **76.42**
- Lead is **not statistically clear**: `contextweaver_v1` score CI [73.0, 79.7] overlaps `contextweaver_v2` [73.0, 79.7]. Treat the ranking as tentative.
- Coverage check: 29.0% of decisions have low support (<5 historical matches).

## Rollout Recommendation

Safety and coverage are hard vetoes: a policy that fails them cannot be `canary`, regardless of score. Thresholds are documented in `docs/evaluation_methodology.md`.

| Policy | Verdict | Why |
|---|---|---|
| contextweaver_v1 | `hold` | low-support share 29.0% exceeds the 20% coverage threshold — the estimate is largely extrapolation |
| contextweaver_v2 | `hold` | low-support share 29.0% exceeds the 20% coverage threshold — the estimate is largely extrapolation |
| baseline | `hold` | unsafe-action rate 4.3% exceeds the 2% safety threshold — hold regardless of score |
| strict_policy | `hold` | low-support share 55.7% exceeds the 20% coverage threshold — the estimate is largely extrapolation |
| cost_aware | `hold` | low-support share 76.3% exceeds the 20% coverage threshold — the estimate is largely extrapolation |

## Confidence Intervals

Seeded bootstrap, 95% interval over 500 resamples.

| Policy | Score (CI) | Success (CI) | Unsafe (CI) |
|---|---|---|---|
| contextweaver_v1 | 76.4 [73.0, 79.7] | 71.00% [66.00%, 75.84%] | 0.33% [0.00%, 1.00%] |
| contextweaver_v2 | 76.4 [73.0, 79.7] | 71.00% [66.00%, 75.84%] | 0.33% [0.00%, 1.00%] |
| baseline | 68.8 [64.8, 72.7] | 65.33% [60.33%, 70.33%] | 4.33% [2.33%, 6.84%] |
| strict_policy | 59.6 [56.0, 63.0] | 44.33% [39.00%, 49.33%] | 0.00% [0.00%, 0.00%] |
| cost_aware | 49.2 [46.5, 52.1] | 22.67% [18.00%, 27.51%] | 0.00% [0.00%, 0.00%] |

## Off-Policy Estimate (IPS / SNIPS)

Estimated average logged reward per policy, from logged rewards and propensities — a different question than the oracle-anchored score. Low-confidence rows rest on thin overlap with the logged actions and should not be trusted as point estimates.

| Policy | IPS | SNIPS | Matched/N | Confidence |
|---|---:|---:|---:|---|
| contextweaver_v1 | 0.708 | 0.836 | 165/300 | ok |
| contextweaver_v2 | 0.708 | 0.836 | 165/300 | ok |
| baseline | 0.850 | 0.661 | 162/300 | ok |
| strict_policy | 0.645 | 0.570 | 107/300 | ok |
| cost_aware | 0.478 | 0.438 | 61/300 | ok |

_Low-confidence off-policy estimates are extrapolation, not measurement: the candidate rarely took the actions the logs recorded, so the importance-weighted sample is thin. They are reported for transparency, not as evidence for rollout._

## Support Diagnostics for `contextweaver_v1`

How often the winner's chosen `(intent, tool)` pairs appear in the logs. Cells below 5 historical matches are flagged: the counterfactual estimate for those decisions is mostly extrapolation and should not be trusted.

| Intent | Tool | Decisions | Historical Support | Trust |
|---|---|---:|---:|---|
| refund_request | billing.issue_refund | 34 | 26 | ok |
| ticket_status | support.search_tickets | 34 | 27 | ok |
| customer_lookup | crm.search_customer | 32 | 26 | ok |
| invoice_question | billing.get_invoice | 27 | 23 | ok |
| policy_lookup | docs.search_policy | 27 | 22 | ok |
| draft_reply | email.draft_reply | 24 | 17 | ok |
| new_issue | billing.issue_refund | 22 | 1 | ⚠️ thin |
| send_reply | email.draft_reply | 21 | 4 | ⚠️ thin |
| audit_export | audit.export_case | 20 | 18 | ok |
| ambiguous | crm.search_customer | 16 | 0 | ⚠️ thin |
| ambiguous | docs.search_policy | 10 | 18 | ok |
| new_issue | crm.search_customer | 6 | 1 | ⚠️ thin |
| refund_request | crm.search_customer | 5 | 3 | ⚠️ thin |
| send_reply | email.send_reply | 5 | 19 | ok |
| new_issue | docs.search_policy | 4 | 1 | ⚠️ thin |
| audit_export | crm.search_customer | 2 | 1 | ⚠️ thin |
| audit_export | support.search_tickets | 2 | 1 | ⚠️ thin |
| refund_request | docs.search_policy | 2 | 4 | ⚠️ thin |
| customer_lookup | docs.search_policy | 1 | 0 | ⚠️ thin |
| draft_reply | email.send_reply | 1 | 2 | ⚠️ thin |
| invoice_question | crm.search_customer | 1 | 1 | ⚠️ thin |
| new_issue | support.search_tickets | 1 | 0 | ⚠️ thin |
| refund_request | support.search_tickets | 1 | 1 | ⚠️ thin |
| send_reply | crm.search_customer | 1 | 1 | ⚠️ thin |
| ticket_status | crm.search_customer | 1 | 4 | ⚠️ thin |

## Dataset Profile

The evaluation read **300** logged decisions. Metrics are only as representative as this input.

- Approval-required decisions: 17.3%

Intent mix:

| Intent | Share |
|---|---:|
| refund_request | 14.0% |
| ticket_status | 11.7% |
| new_issue | 11.0% |
| customer_lookup | 11.0% |
| invoice_question | 9.3% |
| policy_lookup | 9.0% |
| send_reply | 9.0% |
| ambiguous | 8.7% |
| draft_reply | 8.3% |
| audit_export | 8.0% |

Logged failure types:

| Failure type | Share |
|---|---:|
| wrong_tool_selected | 12.0% |
| unsafe_action | 6.0% |
| expensive_tool_selected | 5.0% |
| stale_data_retry | 3.7% |
| ambiguous_request | 2.3% |
| insufficient_tool_coverage | 2.0% |
| over_escalation | 1.7% |
| policy_skipped | 1.3% |

## Outcomes by Intent for `contextweaver_v1`

| Intent | Decisions | Success | Correct Tool | Unresolved |
|---|---:|---:|---:|---:|
| ambiguous | 26 | 38.5% | 38.5% | 61.5% |
| audit_export | 24 | 83.3% | 83.3% | 16.7% |
| customer_lookup | 33 | 97.0% | 97.0% | 0.0% |
| draft_reply | 25 | 96.0% | 96.0% | 4.0% |
| invoice_question | 28 | 96.4% | 96.4% | 3.6% |
| new_issue | 33 | 0.0% | 0.0% | 87.9% |
| policy_lookup | 27 | 100.0% | 100.0% | 0.0% |
| refund_request | 42 | 81.0% | 81.0% | 14.3% |
| send_reply | 27 | 18.5% | 18.5% | 3.7% |
| ticket_status | 35 | 97.1% | 97.1% | 2.9% |

## Pareto Frontier

Policies not dominated by any other across success (↑), unsafe rate (↓), cost (↓), and latency (↓). A policy off the frontier is beaten on every one of those objectives by someone on it.

- `contextweaver_v1`: **on frontier**
- `contextweaver_v2`: **on frontier**
- `baseline`: dominated
- `strict_policy`: **on frontier**
- `cost_aware`: **on frontier**

## What This Cannot Prove

- This is offline replay on synthetic, historical-style logs — not production telemetry. Numbers do not prove production safety.
- Oracle-anchored metrics assume the labelled `oracle_tool` is correct; a mislabelled oracle silently biases every score.
- Off-policy (IPS/SNIPS) estimates are unreliable where a candidate routes into actions the logs rarely took; those rows are flagged, not hidden.
- Offline evaluation cannot capture user adaptation, long-term effects, or live prompt-injection. Pair it with online monitoring, red-teaming, and human review for high-risk actions.

### When NOT to rely on this

- The logs are tiny or unrepresentative of production traffic.
- The winning policy carries a low-support or low-confidence flag.
- The change is high-risk (irreversible writes) and has had no red-team pass.

## Warnings

- **contextweaver_v1**: 29.0% of decisions have low support (<5 historical matches).
- **contextweaver_v1**: skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47).
- **contextweaver_v2**: 29.0% of decisions have low support (<5 historical matches).
- **contextweaver_v2**: skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47).
- **baseline**: 30.7% of decisions have low support (<5 historical matches).
- **baseline**: skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47).
- **strict_policy**: 55.7% of decisions have low support (<5 historical matches).
- **strict_policy**: skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47).
- **cost_aware**: 76.3% of decisions have low support (<5 historical matches).
- **cost_aware**: skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47).

## Notes

- This is offline replay on synthetic historical-style data.
- Use this report as a pre-rollout gate before online A/B tests.