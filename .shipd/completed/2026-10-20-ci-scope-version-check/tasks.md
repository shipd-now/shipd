## 1. CI scope rename

- [x] 1.1 [req: ci-scope-classifier] In `tools/tests/test_ci_scope.py`, change every expectation from `fast=true`/`fast=false` to `scope=content`/`scope=full`, make the `classify` tests assert the returned strings `"content"` and `"full"`, rename tests and the module docstring to say "content scope" and "full scope" instead of "fast", and add a test that the output file's only line is `scope=content` for an epic-only change. Run it and observe it fail.
- [x] 1.2 [req: ci-scope-classifier] In `tools/ci_scope.py`, add constants `CONTENT = "content"` and `FULL = "full"`, make `classify(paths)` return one of them, and make `main` print and write the scope line as the plan's Implementation states; reword the module docstring and the reason text to drop "fast". Confirm 1.1 passes.
- [x] 1.3 [req: ci-fast-path-workflow] In `tools/tests/test_ci_scope.py`, set the guard string to `if: steps.scope.outputs.scope != 'content'`, add "Check the plugin version on main" to the list of unguarded steps, and add a test that `ci.yml` never contains `outputs.fast`. Run it and observe it fail.
- [x] 1.4 [req: ci-fast-path-workflow] In `.github/workflows/ci.yml`, replace every `if: steps.scope.outputs.fast != 'true'` with `if: steps.scope.outputs.scope != 'content'`.

## 2. Main-branch version check

- [x] 2.1 [req: plugin-version-main-check] Create `tools/tests/test_ci_main_version_check.py` (stdlib unittest). Read `.github/workflows/ci.yml`, find the step named "Check the plugin version on main", assert it has `if: github.event_name == 'push'`, mentions `version_guard.py` and `HEAD^1`, and has no `scope` text, and assert the file's `on:` block has `push:` with `branches: [main]`. Extract its run block (lines after `run: |`, dedented) and run it with `bash -e` in a temp git repo that has `plugins/s/.claude-plugin/plugin.json` and a copy of `plugins/s/skills/build/scripts/version_guard.py`: parent `0.6.319`, then a commit editing `plugins/s/skills/build/scripts/x.py` with `0.6.319` must exit non-zero with output holding "base version '0.6.319', head version '0.6.319'" and "follow-up"; the same edit with `0.6.320` must exit 0; a commit editing only `.shipd/epics/x/epic.md` must exit 0. Run it and observe it fail.
- [x] 2.2 [req: plugin-version-main-check] In `.github/workflows/ci.yml`, insert directly after "Guard the plugin version" the step "Check the plugin version on main" with `if: github.event_name == 'push'` and the run block quoted in the plan's Implementation. Confirm 2.1 passes.

## 3. Verify

- [x] 3.1 [req: *] Run `python3 -m unittest discover -s tools/tests -v`, every other suite `ci.yml` runs, `spec_lint.py`, and the docs lint over `docs/`; grep each result for OK or FAILED. Run `version_guard.py --base main --head HEAD` and confirm exit 0 with no bump needed.
