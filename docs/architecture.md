# Architecture

This lab models a support/customer-operations agent with tool-calling behavior. The core flow is:

1. **Logged decisions**: historical-style records with query, intent, available tools, chosen tool, oracle tool, and outcomes.
2. **Candidate policies**: multiple routing strategies (baseline, cost-aware, strict, context-aware).
3. **Offline evaluator**: replays each request with each policy and computes comparable metrics.
4. **Support/coverage checks**: warns when candidate decisions are weakly represented in logs.
5. **Report generation**: emits markdown + terminal summary to inform rollout decisions.

```mermaid
flowchart TD
    L[logged_decisions.csv] --> R1[baseline router]
    L --> R2[cost-aware router]
    L --> R3[strict policy router]
    L --> R4[contextweaver router]
    R1 --> E[evaluator]
    R2 --> E
    R3 --> E
    R4 --> E
    E --> M[metrics]
    E --> S[support warnings]
    M --> REP[report.md]
    S --> REP
    REP --> G[rollout decision]
```

The architecture is local-first and deterministic, so teams can run it in CI before changing production traffic policies.
