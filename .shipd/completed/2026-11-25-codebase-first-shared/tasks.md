# codebase-first-shared — tasks

## 1. The shared rule

- [x] 1.1 [req: headless-contract-reference] Replace the `## Codebase first` body in `plugins/s/skills/ask/references/headless.md` with the engine-neutral rule.
- [x] 1.2 [req: codebase-first-investigation] Reduce the `Codebase-first rule` bodies in `plugins/s/skills/plan/SKILL.md` and `plugins/s/skills/epic/SKILL.md` to a pointer and the interactive application.

## 2. Enrichment reference

- [x] 2.1 [req: enrichment-reference] Move the enrichment loop and re-gate exit from `plugins/s/skills/plan/SKILL.md` into `plugins/s/skills/plan/references/enrichment.md`, leaving the `locate` branch and a pointer.

## 3. Tests and ship

- [x] 3.1 [req: enrichment-reference] In `plugins/s/skills/build/tests/test_external_loaders.py`, pin the merged rule, its engine-neutrality, and the enrichment reference.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` and run every CI unit suite, the spec lint, and `version_guard.py`.
