## 1. Test first

- [x] 1.1 [req: doctor-github-checks] In `plugins/s/skills/build/tests/test_shipd_cli.py`, make the `protection` helper answer the single-branch probe with a 404 when a test passes no `branch`, and give `test_the_github_checks_never_fail_the_preflight` the same canned 404. Add three tests: a 404 with `protected: true` reports `ok`, contains "details need admin access", and does not contain "not protected"; a 404 with `protected: false` warns "not protected"; a 404 with an unreadable branch payload warns "not protected". Run them and confirm the first fails.

## 2. Doctor

- [x] 2.1 [req: doctor-github-checks] In `plugins/s/bin/shipd`, `check_protection`, route a 404 through the `_branch_protected` fallback as plan.md's Implementation describes, keeping the 403 wording and every other path unchanged. Run the test file and confirm it passes.

## 3. Docs and version

- [x] 3.1 [req: doctor-github-checks] In `docs/copilot-review.md`, after the section 5 check table, add one sentence: without admin access the `protection` line is `ok` and says the details need admin access when GitHub still reports the branch protected. Run the docs lint and confirm it is clean.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version by one patch. Run the suites CI runs and confirm they pass.
