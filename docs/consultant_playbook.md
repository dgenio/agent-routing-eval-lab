# Consultant Playbook

Use this lab as a starting framework for client engagements where agents call enterprise tools.

## How to adapt for a client

1. Replace synthetic intents with client-specific request taxonomy.
2. Map real tool catalog metadata (cost, latency, sensitivity, approvals) in
   `src/agent_routing_eval_lab/data/schemas.py::TOOL_CATALOG`. Keep
   `examples/tool_catalog.yaml` in sync — it is the external, human-editable
   mirror, and a drift-guard test fails if the two diverge.
3. Ingest existing logs and define trusted oracle outcomes. Include a
   `propensity_score` and `reward` column if you want honest IPS/SNIPS off-policy
   estimates (see [input-schema.md](input-schema.md)); without them only the
   oracle-anchored metrics are reported.
4. Customize policy candidates. Edit `examples/policy_candidates/*.yaml` and run
   `evaluate --policies examples/policy_candidates/` (needs the `config` extra:
   `pip install -e .[config]`), or add a router to the built-in set in
   `cli.py::_policies`.
5. Reweight score components to match business priorities.
6. Use offline results to decide what reaches canary or production.

## Discovery questions

- What tools can the agent call?
- Which actions are irreversible?
- What does a successful resolution mean?
- What logs already exist?
- Which failures are unacceptable?
- What is the cost of a wrong tool call?
- What requires approval?

## Practical deployment pattern

Run this lab in CI whenever prompts/router/tool-catalog rules change. Treat regressions in safety, unresolved rate, or coverage support as rollout blockers.
