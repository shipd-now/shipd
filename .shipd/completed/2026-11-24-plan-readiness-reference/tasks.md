# plan-readiness-reference — tasks

## 1. The reference and its pointers

- [x] 1.1 [req: plan-readiness-reference] Create
      `plugins/s/skills/plan/references/readiness-rules.md` with the eight parts.
- [x] 1.2 [req: plan-readiness-reference] In `readiness.md`, `plan/SKILL.md`,
      and `emission.md`, replace the moved text with pointers to its headings.
- [x] 1.3 [req: premise-evidence-in-attestation] Fix `emission.md`'s
      Requirements pointer to say an id unique within the change.

## 2. The manifest

- [x] 2.1 [req: external-loader-manifest] In `test_external_loaders.py`, add the
      listing, heading, and prose-only tests, then add the entry to
      `plugins/s/external-loaders.json`.

## 3. Ship

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` and run every CI
      unit suite, the spec lint, and `version_guard.py`.
