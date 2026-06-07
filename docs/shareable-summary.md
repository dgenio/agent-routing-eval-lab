# Shareable Summary

`agent-routing-eval-lab` is an offline evaluation lab for comparing agent routing and tool-selection policies before they affect production traffic. It uses deterministic replay of historical-style decisions to surface trade-offs across quality, cost, latency, unsafe actions, unresolved requests, and support coverage.

## Value Proposition

- Compare candidate routing policies on the same decision set before rollout.
- Catch regressions where one metric improves while safety, cost, latency, or unresolved rate worsens.
- Produce a decision-ready report that supports hold, revise, or canary choices.

## Short Blurb

Offline eval lab for agent routing changes: replay logged support/ops-style decisions, compare candidate policies, and inspect quality, cost, latency, safety, unresolved-rate, and coverage trade-offs before production rollout. Useful for LinkedIn posts, GitHub Discussions, and pre-canary governance conversations.

## Unsafe-Baseline Explanation

Copy-pasteable:

> The baseline policy is included as a reference point, not as a recommended production policy. It is useful because a simple routing policy can look operationally appealing while still carrying hidden trade-offs in unsafe actions, unresolved requests, cost, latency, or support coverage. Offline evaluation makes those trade-offs visible before rollout, but it should be paired with coverage warnings, red-team results, online monitoring, and human judgment for high-risk decisions.

## Architecture Reference

The high-level flow is shown in the README Mermaid diagram:

`Historical logged decisions -> Candidate routing policies -> Offline evaluator -> Metrics + support coverage checks -> Markdown report + terminal summary -> Rollout decision`

For more detail, see [`docs/architecture.md`](architecture.md), which expands the deterministic local replay flow across baseline, cost-aware, strict-policy, and context-aware routers.

## Limitations

- The included data is synthetic demo data, not production telemetry.
- Offline evaluation helps before canary or A/B testing, but it does not replace online experiments.
- High-risk actions still need red-teaming and human review.
- Counterfactual estimates depend on log support and coverage; weakly represented decisions should not be over-interpreted.
- Example metrics are illustrative and should not be treated as universal benchmarks.
