# Contributing

Thanks for helping improve `agent-routing-eval-lab`. This project is a local-first
offline evaluation lab for agent routing and tool-selection policies. Contributions
should make it easier to compare candidate routers on the same logged decisions,
understand quality/cost/latency/safety trade-offs, and produce decision-ready
reports before a production rollout.

## Good First Contribution Areas

- **Metrics**: extend or clarify evaluation metrics in
  `src/agent_routing_eval_lab/evaluation/metrics.py`.
- **Synthetic scenarios**: add realistic logged-decision examples through
  `src/agent_routing_eval_lab/data/generate_synthetic_logs.py` and
  `src/agent_routing_eval_lab/data/schemas.py`.
- **Routers and policies**: improve or add routing strategies under
  `src/agent_routing_eval_lab/routing/`, such as baseline, cost-aware, strict, or
  context-aware policies.
- **Reports and charts**: improve markdown reports in
  `src/agent_routing_eval_lab/evaluation/report.py` or visual outputs in
  `src/agent_routing_eval_lab/visualization/charts.py`.
- **Adapters**: keep optional library integrations honest and explicit in
  `src/agent_routing_eval_lab/adapters/`.
- **Docs**: improve `README.md`, `docs/architecture.md`, and
  `docs/evaluation_methodology.md` when behavior or terminology changes.

## Honesty And Claim Discipline

Keep claims bounded by what the repo demonstrates:

- Synthetic demo data is not production telemetry.
- Offline evaluation can catch regressions before canaries or A/B tests, but it
  does not replace online monitoring, red-teaming, or human review.
- Do not claim production safety, governance guarantees, or full real-world
  readiness from a deterministic demo run.
- Describe `contextweaver` and `skdr-eval` according to the adapter behavior in
  this repo, including fallback behavior when native integrations are unavailable.
- If a change weakens support/coverage assumptions, call that out in docs or the
  generated report rather than hiding the uncertainty.

## Local Commands

These commands are declared by the project `Makefile`:

```bash
make install
make test
make generate-data
make evaluate
make report
make demo
```

Command groups:

- **Install**: `make install` upgrades `pip` and installs the project in editable
  mode with development dependencies.
- **Test**: `make test` runs `pytest`.
- **Generate data**: `make generate-data` writes a sample logged-decisions CSV.
- **Evaluate**: `make evaluate` runs candidate policy evaluation on the sample CSV.
- **Report**: `make report` writes the example markdown report.
- **Demo**: `make demo` runs the end-to-end deterministic demo flow.

Run only the checks that match your change and your local environment. For
documentation-only changes, a markdown review plus `git diff --check` is often
enough before asking for review.

## Backlog Grooming Cadence

Review the open backlog once a month so issues remain actionable for maintainers
and contributors. During that pass:

- Check for duplicate issues and link related reports before closing or merging
  them.
- Make sure every open issue has one priority label and one milestone.
- Keep high-priority issues explicit about dependencies, blockers, and expected
  follow-up work.
- Move exploratory ideas into the future-planning milestone unless they are ready
  for implementation.
- Keep epic issues as umbrella trackers with linked child issues or checklist
  items.

## Pull Request Checklist

- Keep the change scoped to one contribution area when possible.
- Update docs when behavior, metrics, command output, or terminology changes.
- Keep examples reproducible and aligned with committed reports.
- Run the relevant local checks and mention any skipped checks in the PR.
- Preserve the limitations documented in the README and methodology docs.
- Avoid overclaiming safety, governance, or production readiness.
