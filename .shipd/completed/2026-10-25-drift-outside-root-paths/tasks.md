# Tasks

## 1. Tests first

- [x] 1.1 [req: drift-verb] In `plugins/s/skills/build/tests/test_spec_status.py` class `DriftTest`, add `test_path_outside_root_is_skipped`: commit a file, stamp a plan at HEAD citing `src/engine.py`, `../../docs/context-measurement-method/doc.md`, `../scripts`, and `src/../../outside/x.py`, then commit a change to `src/engine.py`. Run `drift feat`; assert exit 4, stderr has no `Error:`, a `file-drift src/engine.py` line prints, and no stdout line names `../`. Add `test_only_outside_root_paths_is_clean`: a plan citing only `../scripts` and `../../docs/a/doc.md` exits 0 with `drift: clean (no findings).`. Add `test_absolute_path_outside_repo_is_skipped`: a plan citing an absolute path under a fresh `tempfile.mkdtemp()` directory (e.g. `<tmp>/outside/doc.md`) plus `src/engine.py`, with no later commit, exits 0 with no `Error:`. Add `test_epic_survives_outside_root_token` only if `DriftTest` already has an epic fixture helper; otherwise skip it. Also add a unit test calling `spec_status._drift_cited(change_dir)` directly on a plan citing `../a/b`, `/abs/c/d`, `x/../../y`, `x/../y/z` and `src/engine.py`, asserting the returned paths are exactly `["x/../y/z", "src/engine.py"]` in citation order. Run the class with `python3 -B -m unittest` and see the new tests fail.

## 2. Fix

- [x] 2.1 [req: drift-verb] In `plugins/s/skills/build/scripts/spec_status.py` `_drift_cited`, after the `./` strip, skip a path when `os.path.isabs(p)` or `posixpath.normpath(p)` is `..` or starts with `../` (import `posixpath` at module top if absent). Keep the original spelling for kept paths. Update the docstring to name the new drop. Re-run `DriftTest` and see it pass.
- [x] 2.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from `0.6.348` to `0.6.349`.
- [x] 2.3 [req: *] Run the full suite `python3 -B -m unittest discover -s plugins/s/skills/build/tests 2>&1 | grep -E "^(OK|FAILED)"` and confirm `OK`.
