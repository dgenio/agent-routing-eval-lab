# Non-Goals and Scope Boundaries

`agent-routing-eval-lab` is deliberately small: it replays logged agent-routing
decisions offline so teams can compare policies before production rollout. These
non-goals help keep that core useful and reviewable.

## Non-Goals

- **Production router or runtime**: the lab compares routing policies offline; a
  production agent runtime should own live routing, retries, permissions,
  secrets, and incident handling.
- **Online experimentation platform**: canaries, A/B tests, live metrics, and
  traffic allocation belong in deployment and experimentation systems. This repo
  prepares a decision before traffic exposure.
- **Hosted service or dashboard product**: reports should remain reproducible
  local artifacts. A hosted UI would add auth, tenancy, storage, and operations
  concerns outside the lab's purpose.
- **General agent framework**: frameworks and orchestration libraries should own
  agent state, tool execution, memory, and runtime control flow. This project
  only needs enough adapters to evaluate routing decisions honestly.
- **Model-serving gateway**: model selection, provider failover, rate limiting,
  and gateway policy are separate infrastructure concerns. The lab may model
  their costs or outcomes, but should not become that gateway.
- **Kitchen-sink evaluation suite**: new metrics should support routing and
  tool-selection decisions. Broad benchmark coverage is useful, but outside this
  repo unless it improves the offline routing comparison.

## Revisiting a Boundary

A non-goal can change if the project direction changes. Open an issue with the
use case, evidence, expected maintenance cost, and why the need is not better
served by a sibling tool or integration.
