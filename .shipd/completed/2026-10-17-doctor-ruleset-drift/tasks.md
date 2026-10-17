## 1. Protection reads rulesets

- [x] 1.1 [req: doctor-github-checks] In `plugins/s/skills/build/tests/test_shipd_cli.py` (GitHub-side checks section, near `test_unprotected_default_branch_warns`), add tests: classic 404 plus the branch-rules API response listing a `required_status_checks` rule with `semantic-review` gives `ok protection` naming a ruleset; a non-empty rules list without the context gives `warn` naming the ruleset and not "not protected"; classic 404 plus an empty list `[]` still warns not protected; a failing rules probe leaves the classic outcome. Run them and observe failure.
- [x] 1.2 [req: doctor-github-checks] Update the existing protection tests in that file whose stub responses lack the new branch-rules probe key (the string `"rules/branches/main"` in the stub map) (the stub fails on unexpected calls): add an entry for that key returning `self.ok_json([])` to their probes.
- [x] 1.3 [req: doctor-github-checks] In `plugins/s/bin/shipd`, add `_branch_rules(context, branch, run)` returning `(status, list)` from the GitHub branch-rules endpoint (repos, nwo, rules, branches, branch), and rework `check_protection` per plan.md: union the contexts of classic protection and `required_status_checks` rules, ok naming the source, warn naming a ruleset when protected without the context, "not protected" only when both sources are empty; confirm 1.1 and 1.2 pass.

## 2. Drift and Actions checks

- [x] 2.1 [req: doctor-merge-rules-check, doctor-actions-approve-check] In the same test file add tests for `check_merge_rules` and `check_actions_approve` covering every scenario in the delta spec, using a fake runner and a fake `merge_rules` module injected by the `merge_rules` argument; run and observe failure.
- [x] 2.2 [req: doctor-merge-rules-check] In `plugins/s/bin/shipd` add `check_merge_rules(root, context, run=_gh_run, merge_rules=None)` per plan.md, loading the module with the `_load_merge_rules` loader added by `merge-rules-config`.
- [x] 2.3 [req: doctor-actions-approve-check] In `plugins/s/bin/shipd` add `check_actions_approve(root, context, run=_gh_run)` per plan.md.
- [x] 2.4 [req: doctor-merge-rules-check, doctor-actions-approve-check] Append `("merge-rules", ...)` and `("actions-approve", ...)` thunks after `fast-pass` in `check_steps`, and update the expected name lists in `test_shipd_cli.py` (the tuple near line 1309 and the tails asserted near lines 2125 and 2832).
- [x] 2.5 [req: doctor-new-checks-report-only] Add a test that `--fix` runs no `gh` mutation for a `warn merge-rules` line and prints a `/s:gate` fix hint; add the two names to the fix-surface mapping in `plugins/s/bin/shipd` (`REMEDY_SURFACES`, and the fix-hint branch that names `/s:gate` for `protection`) so the hint names `/s:gate`.

## 3. Skill, docs, release

- [x] 3.1 [req: doctor-ruleset-lines] In `plugins/s/skills/doctor/SKILL.md` add `merge-rules` and `actions-approve` to the parsed check list, two report-only rows (`/s:gate`, `shipd gate rules apply`), and a sentence that a ruleset-sourced `protection` warning gets no classic PUT or POST.
- [x] 3.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` by one patch above `main`'s value at build time and run `version_guard.py --base main --head HEAD`.
- [x] 3.3 [req: *] Run the full suite for `plugins/s/skills/build/tests` and confirm no failures (grep for OK or FAILED).
