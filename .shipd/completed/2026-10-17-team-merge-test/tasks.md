## 1. Prerequisites gate (live, read-only)

- [x] 1.1 [req: merge-proof-driver] Run `gh api repos/mikkel-bergmann/unkannybanny/collaborators --jq '.[].login'`, `gh api repos/mikkel-bergmann/unkannybanny/actions/permissions/workflow`, and check `TEAM_TEST_REVIEWER_GH_TOKEN` or `TEAM_TEST_REVIEWER_GH_CONFIG_DIR` is set (test presence only, never print it). If the second account is not a collaborator with write, its credential variable is unset, or Actions approval is false, STOP and tell the user to: add the second account as write collaborator and accept; export its token in their own shell; and consent to the Actions setting (`/s:gate`'s optional row). Do not continue until all hold.
- [x] 1.2 [req: merge-proof-driver] Confirm the earlier members are merged: `plugins/s/bin/shipd gate rules --help` exits 0 and `plugins/s/bin/shipd room whoami --help` exits 0. If not, STOP.

## 2. Driver

- [x] 2.1 [req: merge-proof-driver] Create `tools/tests/test_team_merge_test.py` (unittest, fake `Gh` runner) covering repo refusal, preflight missing lines and exit 3, `redact`, `classify_probe` (405 blocked, 200 merged), and `approvals_on_head`. Run it and see it fail.
- [x] 2.2 [req: merge-proof-driver] Create `tools/team_merge_test.py` with `ALLOWED_REPO`, `Gh`, the pure helpers, and the `preflight` verb per plan.md until 2.1 passes.
- [x] 2.3 [req: merge-proof-scenarios] Extend the test file with a scripted fake-runner run of all six steps (pass path, plus a failing step that stops and leaves evidence), and `render_report` output. See it fail.
- [x] 2.4 [req: merge-proof-scenarios] Add the `apply`, `run`, and `report` verbs to `tools/team_merge_test.py` per plan.md until 2.3 passes. Run `python3 -m unittest discover -s tools/tests`.

## 3. Documentation

- [x] 3.1 [req: merge-proof-docs] Create `docs/team-merge-test.md` (first line `<!-- doc-type: how-to -->`, at most 150 lines): prerequisites, the env variable names, the prep PR, and the four verbs. Run `plugins/s/skills/document/scripts/docs_lint.py docs/team-merge-test.md` until clean.

## 4. Live proof (unkannybanny only)

- [x] 4.1 [req: merge-proof-driver] Prep PR on unkannybanny from `/Users/mikkelbergmann/projects/workspaces/unkannybanny/unkannybanny`: `shipd copilot add`, add the explicit `merge` block to `.shipd-config.json`, ship through unkannybanny's own flow, wait for merge. Then run `python3 tools/team_merge_test.py preflight` and require exit 0.
- [x] 4.2 [req: merge-proof-scenarios] Run `python3 tools/team_merge_test.py apply`, then `run --out <scratchpad>/evidence`. If a step fails, keep the PR open, report the failing evidence line, and stop.
- [x] 4.3 [req: merge-proof-docs] Run `report` into `docs/retros/<run-date>-team-merge-test.md` and link the merged pull request URL in it. Confirm no token text appears (`grep` the file for the variable names' values is not needed; check it holds no `ghp_` or `github_pat_`).
- [x] 4.4 [req: *] Run `python3 -m unittest discover -s tools/tests` and confirm no failures.
