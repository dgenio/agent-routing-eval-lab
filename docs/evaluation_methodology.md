# Evaluation Methodology

## Metrics

The evaluator computes:

- **Success rate**: share of requests resolved successfully.
- **Correct tool selection rate**: share where candidate tool matches oracle tool.
- **Average cost**: mean estimated tool execution cost.
- **Average latency**: mean estimated latency in milliseconds.
- **Unsafe action rate**: share of risky actions (e.g., refund without approval).
- **Approval-required action rate**: share of selected tools requiring approvals.
- **Unresolved request rate**: share of requests left unresolved.
- **Estimated regret vs oracle**: utility gap between candidate and oracle routing.
- **Support/coverage warning**: warning if many candidate actions have low support in historical logs.
- **Composite score**: weighted score balancing quality, safety, cost, and latency.

## Support/Coverage Risk

Offline estimates are less trustworthy where candidate decisions are rare in historical logs. This repo computes support as count of historical `(intent, chosen_tool)` matches and warns when low-support share is high.

## Why offline evaluation matters

Offline evaluation catches policy regressions earlier and cheaper than production rollouts. It is useful before canary/A-B tests, but it is not enough alone:

- It depends on log quality and representativeness.
- It cannot fully capture user adaptation or long-term effects.
- It should be paired with online monitoring, red-teaming, and human governance.
