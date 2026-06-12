# Public Roadmap

Last reviewed: 2026-06-12

This roadmap organizes the open backlog into five public themes with rough
sequencing and dependency notes. It is directional guidance, not a promise of
delivery dates.

## Always true constraints

- Keep a zero-dependency, deterministic, local-first core for the default path.
- Keep claim discipline: offline replay is a pre-rollout gate, not production proof.
- Keep scope discipline from docs/non-goals.md and avoid kitchen-sink expansion.
- Keep contribution pathways explicit through linked issues and milestone hygiene.

## Update policy

- Review quarterly or when preparing a release.
- Update this file's date, issue counts, and sequencing notes during each review.
- Move links when priorities change, but do not hide unresolved work.
- If this file becomes stale, open a docs issue and tag contributor-experience.

## Rough sequencing

1. Now: Theme 1 and Theme 2 (M1 and M2)
2. Next: Theme 4 (M3)
3. Then: Theme 3 (M4)
4. Later: Theme 5 (M5)

## Dependency notes

- Issue #103 depends on #113 (completed) and is related to #79 (completed).
- Theme 4 depends on Theme 1 and Theme 2 guardrails.
- Theme 3 depends on Theme 4 contracts (gate outputs, CI receipts, packaging hygiene).

## Theme 1: Honest off-policy evaluation

Goal: keep evaluator behavior honest, deterministic, and defensible.
Current state: active foundation work in M1.
Help wanted here: parsing hardening, deterministic output controls, and integrity checks.

Open issues mapped (16):
[#2](https://github.com/dgenio/agent-routing-eval-lab/issues/2), [#10](https://github.com/dgenio/agent-routing-eval-lab/issues/10), [#11](https://github.com/dgenio/agent-routing-eval-lab/issues/11), [#14](https://github.com/dgenio/agent-routing-eval-lab/issues/14), [#36](https://github.com/dgenio/agent-routing-eval-lab/issues/36), [#41](https://github.com/dgenio/agent-routing-eval-lab/issues/41), [#62](https://github.com/dgenio/agent-routing-eval-lab/issues/62), [#70](https://github.com/dgenio/agent-routing-eval-lab/issues/70), [#71](https://github.com/dgenio/agent-routing-eval-lab/issues/71), [#72](https://github.com/dgenio/agent-routing-eval-lab/issues/72), [#75](https://github.com/dgenio/agent-routing-eval-lab/issues/75), [#83](https://github.com/dgenio/agent-routing-eval-lab/issues/83), [#84](https://github.com/dgenio/agent-routing-eval-lab/issues/84), [#88](https://github.com/dgenio/agent-routing-eval-lab/issues/88), [#112](https://github.com/dgenio/agent-routing-eval-lab/issues/112), [#125](https://github.com/dgenio/agent-routing-eval-lab/issues/125)

## Theme 2: Unsafe -> governed narrative

Goal: make unsafe baseline risks and governed mitigations visible and testable.
Current state: active narrative and behavior work in M2.
Help wanted here: governed-path demos, security scenarios, and behavior tests.

Open issues mapped (19):
[#3](https://github.com/dgenio/agent-routing-eval-lab/issues/3), [#5](https://github.com/dgenio/agent-routing-eval-lab/issues/5), [#8](https://github.com/dgenio/agent-routing-eval-lab/issues/8), [#20](https://github.com/dgenio/agent-routing-eval-lab/issues/20), [#21](https://github.com/dgenio/agent-routing-eval-lab/issues/21), [#22](https://github.com/dgenio/agent-routing-eval-lab/issues/22), [#23](https://github.com/dgenio/agent-routing-eval-lab/issues/23), [#24](https://github.com/dgenio/agent-routing-eval-lab/issues/24), [#25](https://github.com/dgenio/agent-routing-eval-lab/issues/25), [#26](https://github.com/dgenio/agent-routing-eval-lab/issues/26), [#27](https://github.com/dgenio/agent-routing-eval-lab/issues/27), [#28](https://github.com/dgenio/agent-routing-eval-lab/issues/28), [#29](https://github.com/dgenio/agent-routing-eval-lab/issues/29), [#30](https://github.com/dgenio/agent-routing-eval-lab/issues/30), [#32](https://github.com/dgenio/agent-routing-eval-lab/issues/32), [#33](https://github.com/dgenio/agent-routing-eval-lab/issues/33), [#34](https://github.com/dgenio/agent-routing-eval-lab/issues/34), [#37](https://github.com/dgenio/agent-routing-eval-lab/issues/37), [#38](https://github.com/dgenio/agent-routing-eval-lab/issues/38)

## Theme 3: Real-library showcase

Goal: make ecosystem integrations credible, reproducible, and easy to adopt.
Current state: major integration and packaging work in M4.
Help wanted here: adapter contracts, compatibility CI, and onboarding docs.

Open issues mapped (29):
[#4](https://github.com/dgenio/agent-routing-eval-lab/issues/4), [#12](https://github.com/dgenio/agent-routing-eval-lab/issues/12), [#13](https://github.com/dgenio/agent-routing-eval-lab/issues/13), [#15](https://github.com/dgenio/agent-routing-eval-lab/issues/15), [#16](https://github.com/dgenio/agent-routing-eval-lab/issues/16), [#35](https://github.com/dgenio/agent-routing-eval-lab/issues/35), [#46](https://github.com/dgenio/agent-routing-eval-lab/issues/46), [#47](https://github.com/dgenio/agent-routing-eval-lab/issues/47), [#48](https://github.com/dgenio/agent-routing-eval-lab/issues/48), [#49](https://github.com/dgenio/agent-routing-eval-lab/issues/49), [#50](https://github.com/dgenio/agent-routing-eval-lab/issues/50), [#51](https://github.com/dgenio/agent-routing-eval-lab/issues/51), [#52](https://github.com/dgenio/agent-routing-eval-lab/issues/52), [#53](https://github.com/dgenio/agent-routing-eval-lab/issues/53), [#61](https://github.com/dgenio/agent-routing-eval-lab/issues/61), [#77](https://github.com/dgenio/agent-routing-eval-lab/issues/77), [#78](https://github.com/dgenio/agent-routing-eval-lab/issues/78), [#81](https://github.com/dgenio/agent-routing-eval-lab/issues/81), [#82](https://github.com/dgenio/agent-routing-eval-lab/issues/82), [#85](https://github.com/dgenio/agent-routing-eval-lab/issues/85), [#92](https://github.com/dgenio/agent-routing-eval-lab/issues/92), [#96](https://github.com/dgenio/agent-routing-eval-lab/issues/96), [#97](https://github.com/dgenio/agent-routing-eval-lab/issues/97), [#99](https://github.com/dgenio/agent-routing-eval-lab/issues/99), [#101](https://github.com/dgenio/agent-routing-eval-lab/issues/101), [#102](https://github.com/dgenio/agent-routing-eval-lab/issues/102), [#104](https://github.com/dgenio/agent-routing-eval-lab/issues/104), [#105](https://github.com/dgenio/agent-routing-eval-lab/issues/105), [#121](https://github.com/dgenio/agent-routing-eval-lab/issues/121)

## Theme 4: CI-gate productization

Goal: turn evaluator outputs into reliable operator and CI decision gates.
Current state: operator UX and productization work in M3.
Help wanted here: command ergonomics, structured outputs, and CI-ready artifacts.

Open issues mapped (26):
[#7](https://github.com/dgenio/agent-routing-eval-lab/issues/7), [#9](https://github.com/dgenio/agent-routing-eval-lab/issues/9), [#56](https://github.com/dgenio/agent-routing-eval-lab/issues/56), [#57](https://github.com/dgenio/agent-routing-eval-lab/issues/57), [#58](https://github.com/dgenio/agent-routing-eval-lab/issues/58), [#59](https://github.com/dgenio/agent-routing-eval-lab/issues/59), [#60](https://github.com/dgenio/agent-routing-eval-lab/issues/60), [#63](https://github.com/dgenio/agent-routing-eval-lab/issues/63), [#64](https://github.com/dgenio/agent-routing-eval-lab/issues/64), [#65](https://github.com/dgenio/agent-routing-eval-lab/issues/65), [#66](https://github.com/dgenio/agent-routing-eval-lab/issues/66), [#67](https://github.com/dgenio/agent-routing-eval-lab/issues/67), [#68](https://github.com/dgenio/agent-routing-eval-lab/issues/68), [#69](https://github.com/dgenio/agent-routing-eval-lab/issues/69), [#73](https://github.com/dgenio/agent-routing-eval-lab/issues/73), [#80](https://github.com/dgenio/agent-routing-eval-lab/issues/80), [#87](https://github.com/dgenio/agent-routing-eval-lab/issues/87), [#89](https://github.com/dgenio/agent-routing-eval-lab/issues/89), [#98](https://github.com/dgenio/agent-routing-eval-lab/issues/98), [#109](https://github.com/dgenio/agent-routing-eval-lab/issues/109), [#114](https://github.com/dgenio/agent-routing-eval-lab/issues/114), [#115](https://github.com/dgenio/agent-routing-eval-lab/issues/115), [#116](https://github.com/dgenio/agent-routing-eval-lab/issues/116), [#117](https://github.com/dgenio/agent-routing-eval-lab/issues/117), [#120](https://github.com/dgenio/agent-routing-eval-lab/issues/120), [#122](https://github.com/dgenio/agent-routing-eval-lab/issues/122)

## Theme 5: Bring-your-own-data

Goal: broaden input realism and data pathways while keeping offline determinism.
Current state: deferred and exploratory work in M5.
Help wanted here: data import validation, scalability experiments, and sample-size guidance.

Open issues mapped (12):
[#86](https://github.com/dgenio/agent-routing-eval-lab/issues/86), [#93](https://github.com/dgenio/agent-routing-eval-lab/issues/93), [#94](https://github.com/dgenio/agent-routing-eval-lab/issues/94), [#95](https://github.com/dgenio/agent-routing-eval-lab/issues/95), [#100](https://github.com/dgenio/agent-routing-eval-lab/issues/100), [#106](https://github.com/dgenio/agent-routing-eval-lab/issues/106), [#107](https://github.com/dgenio/agent-routing-eval-lab/issues/107), [#108](https://github.com/dgenio/agent-routing-eval-lab/issues/108), [#110](https://github.com/dgenio/agent-routing-eval-lab/issues/110), [#111](https://github.com/dgenio/agent-routing-eval-lab/issues/111), [#123](https://github.com/dgenio/agent-routing-eval-lab/issues/123), [#124](https://github.com/dgenio/agent-routing-eval-lab/issues/124)

## Coverage accounting

- Open issues in snapshot: 102
- Issues linked in this roadmap: 102
- Coverage: 100%
- Acceptance target from issue #103: >=90%
