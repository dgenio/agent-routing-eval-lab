# Consultant Playbook

Use this lab as a starting framework for client engagements where agents call enterprise tools.

## How to adapt for a client

1. Replace synthetic intents with client-specific request taxonomy.
2. Map real tool catalog metadata (cost, latency, sensitivity, approvals).
3. Ingest existing logs and define trusted oracle outcomes.
4. Customize policy candidates (router prompts, model, tool cards, governance rules).
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
