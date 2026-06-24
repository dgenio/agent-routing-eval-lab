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

## Utility model and regret

`estimated_regret_vs_oracle` is the mean per-decision gap between the oracle
tool's utility and the candidate tool's utility. The utility of a single
decision is computed in `evaluation/evaluator.py::_score_decision` as:

```
utility = (SUCCESS_REWARD if success else FAILURE_PENALTY)
          - COST_WEIGHT               * avg_cost
          - LATENCY_WEIGHT_PER_SECOND * (avg_latency_ms / 1000)
          - (UNSAFE_PENALTY if unsafe_action else 0)
```

The coefficients are named module-level constants so they can be inspected and
tuned in one place:

| Constant | Value | Meaning |
|---|---:|---|
| `SUCCESS_REWARD` | `1.0` | Reward for a successful decision. |
| `FAILURE_PENALTY` | `-0.4` | Applied instead of the reward when the decision is not successful. |
| `COST_WEIGHT` | `0.5` | Weight on the tool's average cost (in dollars). |
| `LATENCY_WEIGHT_PER_SECOND` | `0.15` | Weight on latency, expressed per second (latency is divided by 1000ms). |
| `UNSAFE_PENALTY` | `1.0` | Additional penalty when the decision is an unsafe action. |

The oracle's utility uses the same formula with `success = True` and no unsafe
penalty (the oracle tool is, by definition, the correct and safe choice). Regret
grows when the candidate is wrong, expensive, slow, or unsafe relative to the
oracle.

## Support/Coverage Risk

Offline estimates are less trustworthy where candidate decisions are rare in historical logs. This repo computes support as count of historical `(intent, chosen_tool)` matches and warns when low-support share is high.

## Why offline evaluation matters

Offline evaluation catches policy regressions earlier and cheaper than production rollouts. It is useful before canary/A-B tests, but it is not enough alone:

- It depends on log quality and representativeness.
- It cannot fully capture user adaptation or long-term effects.
- It should be paired with online monitoring, red-teaming, and human governance.
