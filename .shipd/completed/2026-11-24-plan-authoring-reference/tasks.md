# plan-authoring-reference — tasks

## 1. The reference and its pointers

- [x] 1.1 [req: plan-authoring-reference] Create
      `plugins/s/skills/plan/references/authoring.md` with the eight parts.
- [x] 1.2 [req: plan-authoring-reference] In
      `plugins/s/skills/plan/references/emission.md` and `readiness.md`,
      replace the moved prose with pointers to the `authoring.md` headings.
- [x] 1.3 [req: plan-authoring-reference] In
      `plugins/s/skills/plan/SKILL.md`, add the file to the path list and to
      the emit step.

## 2. The manifest

- [x] 2.1 [req: external-loader-manifest] In
      `plugins/s/skills/build/tests/test_external_loaders.py`, add the listing
      and prose-only tests, then add the entry to
      `plugins/s/external-loaders.json`.

## 3. Ship

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` and run every CI
      unit suite, the spec lint, and `version_guard.py`.
