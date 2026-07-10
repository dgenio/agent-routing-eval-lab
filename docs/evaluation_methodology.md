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

## Decision-time information (leakage guard)

Candidate policies act only on information available at decision time. The
evaluator hands each router a metadata dict containing **only** decision-time
context — currently `approval_granted` — and deliberately never includes
`oracle_tool` (the ground-truth answer). Leaking the oracle would let any router
(custom or accidental) return it and score a perfect correct-tool rate,
invalidating every comparison the lab exists to make.

The metadata contract for `Router.route(...)` is documented in
`agent_routing_eval_lab.routing` and enforced by a regression test
(`tests/test_evaluator.py::test_routers_never_receive_oracle_tool_metadata`),
which asserts routers never receive `oracle_tool` and always receive
`approval_granted`.

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

## Two questions, two methods

The lab reports **two distinct views** of each candidate policy. They answer
different questions and must not be conflated:

1. **Oracle-anchored scenario replay** — every metric in the comparison table
   (`success_rate`, `correct_tool_selection_rate`, `estimated_regret_vs_oracle`,
   the composite `score`, etc.). These score the candidate's tool choice against
   the labelled `oracle_tool` and the catalog utility model. They answer *"did
   the candidate pick the tool we labelled correct, and how good is that tool?"*
   They do **not** use the logged outcomes, so they cannot on their own prove the
   candidate would have earned good rewards on real traffic.

2. **Off-policy value estimation (IPS / SNIPS)** — `evaluation/off_policy.py`.
   This answers the genuinely counterfactual question *"what average logged
   reward would this candidate have earned on the logged traffic?"* using only
   the logged `reward` and the behavior policy's `propensity_score`:

   ```
   V_IPS(π)   = (1/n) · Σ_i  [π(a_i | x_i) / μ(a_i | x_i)] · r_i
   V_SNIPS(π) =  Σ_i w_i r_i  /  Σ_i w_i          where w_i = π(a_i|x_i)/μ(a_i|x_i)
   ```

   Because the candidate routers are deterministic, `π(a_i | x_i)` is 1 when the
   candidate reproduces the logged action `a_i` and 0 otherwise, so IPS averages
   `reward / propensity` over the overlapping rows and 0 elsewhere. SNIPS
   self-normalizes to reduce variance.

### What the off-policy estimate can and cannot prove

- It **can** estimate a candidate's expected reward without deploying it, when
  the logs record honest propensities and rewards and the candidate's actions
  overlap the logged actions.
- It **cannot** say anything reliable where the candidate routes into actions the
  logs rarely or never took. The estimator reports the effective sample size and
  the match rate, and **flags the estimate `low_confidence`** (a
  `estimator.low_confidence` warning) rather than presenting a high-variance
  extrapolation as certain. This is deliberately the opposite of substituting
  oracle truth for missing support.
- When the logs carry no `propensity_score`/`reward` columns, the estimate is
  marked unavailable (`estimator.ips_unavailable`) and only the oracle-anchored
  metrics are reported. Nothing is silently faked.

The optional native `skdr-eval` doubly-robust cross-check is tracked in issue #47
and is not wired here; the adapter says so explicitly instead of pretending.

## Composite score and its weights

The comparison table's `score` is a single, business-tunable weighted average on a
0-100 scale. Each term is either a quality rate or `1 - badness`, so higher is
always better:

```
score = 100 · (
    w_success    · success_rate
  + w_correct    · correct_tool_selection_rate
  + w_safety     · (1 - unsafe_action_rate)
  + w_unresolved · (1 - unresolved_request_rate)
  + w_cost       · (1 - normalized_cost)
  + w_latency    · (1 - normalized_latency)
)
```

`normalized_cost`/`normalized_latency` divide the average cost/latency by the
catalog-wide maximum (a fixed, policy-independent bound so scores stay comparable
across policies and runs).

Default weights and rationale (they sum to 1.0):

| Weight | Default | Why |
|---|---:|---|
| `success` | 0.40 | Resolving the request correctly is the primary goal. |
| `correct_tool` | 0.20 | Routing quality signal, weighted below end-to-end success. |
| `safety` | 0.15 | Soft score term; **hard** safety vetoes live in the rollout recommendation, not here. |
| `unresolved` | 0.10 | Penalizes requests left hanging even without a wrong action. |
| `cost` | 0.075 | Efficiency term on catalog-normalized cost. |
| `latency` | 0.075 | Efficiency term on catalog-normalized latency. |

The right weighting is domain-specific (a refund agent weights `safety` far higher
than a docs-search agent), so the weights are **configurable without editing
source**: pass `--weights weights.json` to `evaluate`/`report` with any subset of
these keys. The defaults live in `ScoreWeights` (`evaluation/metrics.py`).

## Confidence intervals

Point scores hide whether one policy is meaningfully ahead or just noise on a
small log. The evaluator computes seeded **bootstrap** confidence intervals
(`evaluation/confidence.py`) for `score`, `success_rate`, `unsafe_action_rate`,
`average_cost`, and `average_latency_ms` by resampling the scored decisions with
replacement. The report marks the winner's lead as *clear* only when its score
interval does not overlap the runner-up's. Intervals are deterministic for a fixed
seed.

## Support/Coverage Risk

Offline estimates are less trustworthy where candidate decisions are rare in historical logs. This repo computes support as count of historical `(intent, chosen_tool)` matches and warns when low-support share is high.

## Why offline evaluation matters

Offline evaluation catches policy regressions earlier and cheaper than production rollouts. It is useful before canary/A-B tests, but it is not enough alone:

- It depends on log quality and representativeness.
- It cannot fully capture user adaptation or long-term effects.
- It should be paired with online monitoring, red-teaming, and human governance.
