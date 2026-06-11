# Glossary

This glossary defines the terms used by `agent-routing-eval-lab` when comparing routing and tool-selection policies offline.

## Agent routing

The decision layer that maps a user request, inferred intent, available tools, and optional metadata to one selected tool. In this repo, routers implement that decision in `src/agent_routing_eval_lab/routing/`.

## Tool selection

The concrete choice of a tool name from the tools available for a logged request. The evaluator compares each candidate tool against the row's `oracle_tool` and then scores quality, cost, latency, safety, unresolved rate, and support coverage.

## Tool-calling agent

An agent that can act by choosing external tools instead of only producing text. This lab models the routing part of that behavior; it does not execute real tools against production systems.

## MCP-style tools

Structured tools exposed to an agent through a catalog-like interface. The sample catalog in `examples/tool_catalog.yaml` and `TOOL_CATALOG` in `src/agent_routing_eval_lab/data/schemas.py` model tool names, cost, latency, sensitivity, and approval requirements.

## Offline evaluation

Evaluation performed before production rollout by replaying historical-style logged decisions through candidate routing policies. It can reveal trade-offs before online A/B tests, but it cannot replace live monitoring, red-team review, or human judgment.

## Logged decision

A row in `examples/logged_decisions.sample.csv` containing a request, inferred intent, available tools, historical chosen tool, oracle tool, outcome fields, approval metadata, and cost/latency values. Logged decisions are the shared input used to compare candidate policies.

## Candidate policy

A router or policy configuration being evaluated against the same logged decisions as the other candidates. Examples include `baseline`, `strict_policy`, `cost_aware`, and `contextweaver_v1`.

## Unsafe baseline

A simple reference policy that may look operationally convenient but can hide safety, cost, latency, support coverage, or unresolved-request trade-offs. In this repo, the baseline is useful as a comparison point, not as a recommended production policy.

## Governed path

A rollout path that uses offline evaluation results, support coverage warnings, safety metrics, and human review before a routing policy reaches production traffic. The README frames this as hold, revise, or canary rather than automatic deployment.

## Context firewall

A boundary that keeps routing inputs focused on the request, intent, available tools, and approved metadata instead of exposing unnecessary context or every possible tool schema. In this lab, bounded tool cards are the main example of that boundary.

## Bounded choice card

A compact list of permitted tool choices given to a router for a decision. The `ContextWeaverRouter` uses bounded cards from `contextweaver_adapter.py` and then picks from available tools while avoiding sensitive or approval-gated tools when approval is absent.

## Support/coverage warning

A warning that a candidate policy is making too many decisions in weakly represented regions of the logs. The evaluator computes support as the count of historical `(intent, chosen_tool)` matches and, by default, treats fewer than `5` matches as low support.

## Oracle tool

The expected best tool for a logged decision. It is stored as `oracle_tool` in the sample CSV, must exist in `TOOL_CATALOG`, and is used to calculate correct tool rate and estimated regret.

## Regret

The estimated utility gap between the candidate-selected tool and the oracle tool. In this repo, `estimated_regret_vs_oracle` is computed from the difference between `utility_oracle` and `utility_candidate` across scored rows.

## Approval-required action

A tool choice that requires approval according to the tool catalog. For example, `billing.issue_refund` and `audit.export_case` are marked as approval-required; selecting them without approval contributes to unsafe-action behavior.
