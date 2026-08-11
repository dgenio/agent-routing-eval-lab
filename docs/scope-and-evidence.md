# Scope and evidence: MEASURE IT

The Routing Eval Lab has one portfolio job: **MEASURE IT**.

It should help a team decide whether a routing-policy change is supported by its logged data before rollout. It is not a general benchmark zoo, an LLM-router playground, or an integration showcase for the whole dgenio ecosystem.

## Canonical library scope

Only two OSS components are part of the core story:

- `contextweaver` — candidate routing / bounded ChoiceCard behavior;
- `skdr-eval` — offline evaluation, support/overlap diagnostics, and decision evidence.

The default/reference path may remain fully offline, but any `real` result must come from the native packages and record their provenance. A real run must fail rather than silently fall back.

## What the lab should prove

The strongest result is not automatically `ROLL OUT`.

The lab should preserve cases where a candidate looks attractive on a point estimate but the evidence says **HOLD** because overlap, support, effective sample size, uncertainty, or another documented diagnostic is inadequate.

Reports should distinguish:

- observed behavior in the logged data;
- estimated candidate value/effect;
- evidence/support diagnostics;
- uncertainty and failure modes;
- rollout recommendation (`HOLD`, `REVISE`, `CANARY`, or equivalent);
- limitations of offline evidence.

Synthetic datasets are teaching fixtures, not external validation.

## Next adoption step

After native integration is trustworthy, the next useful surface is **bring your own logged decisions**.

A local user-log path should eventually:

1. accept a documented portable format;
2. validate required fields and reject malformed data;
3. provide a safe local scrubbing/redaction step for sensitive columns;
4. run the same support diagnostics and candidate comparison;
5. emit a portable report/receipt that identifies versions and execution mode.

That is higher priority than adding more synthetic domains, plots, hosted telemetry, LLM routers, notebooks, leaderboards, or framework integrations.

## Scope gate

Do not add a metric, estimator, domain pack, visualization, integration, or policy because it is interesting. Add it when it materially improves a real routing decision, addresses a methodological blind spot, or responds to external user evidence.

If people run the lab but do not use the evaluation path on their own data, improve the input format, interpretation, or product bridge. Do not respond by multiplying scenarios.

After two serious distribution experiments with essentially no downstream use, freeze the lab as a stable educational reference.

## Relationship to sibling labs

- `mcp-agent-security-dojo` — **BREAK IT**: failures and mitigations.
- this repo — **MEASURE IT**: routing-change evidence.
- `enterprise-agent-control-plane` — **ASSEMBLE IT**: later composition of already-useful controls.
