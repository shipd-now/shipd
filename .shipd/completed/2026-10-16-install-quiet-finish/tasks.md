# Tasks — install-quiet-finish

- [x] 1 [req: install-doctor-finish] In `plugins/s/bin/shipd`, add `check_steps(root)` returning the eighteen checks as ordered `(name, thunk)` pairs (today's `default_checks` order, GitHub context resolved lazily once on the first GitHub-side thunk), and rewrite `default_checks(root)` as `[thunk() for _name, thunk in check_steps(root)]`. Add a test in `plugins/s/skills/build/tests/test_shipd_cli.py` that `check_steps` names match the `default_checks` result names in order. The existing `doctor` tests stay green.
- [x] 2 [req: install-doctor-finish] In `plugins/s/skills/build/tests/test_shipd_cli.py`, rewrite `DoctorFinishTest` against the new `doctor_finish(handle, root=None, steps=None, run=default_run)` seam per `plan.md` `## Implementation`, with fabricated steps and a fake `run`: all-ok writes `[i/n]` progress and `✓ n of n checks ok` with no per-check line; a successful `difft` remedy runs once, re-runs the check, and leaves no `difft`, `/s:doctor`, or `semdiff doctor` text; a failed remedy writes `automatic install failed: <reason>` plus a `fix:` line; a `protection` warn runs no remedy and writes its line plus `fix:`; a `fail` check writes its line and `fix:` and returns `None`; defaults resolve to `check_steps` and `os.getcwd()`. Observe the new tests fail.
- [x] 3 [req: install-doctor-finish] In `plugins/s/bin/shipd`, implement the new `doctor_finish` per `plan.md` `## Implementation` — progress line, silent remedies with re-check, `FINISH_FIXES` table, summary and per-problem lines — and delete `INSTALL_FINISH_POINTER`. All of `test_shipd_cli.py` passes.
- [x] 4 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` from `0.6.304` to `0.6.305`.
- [x] 5 [req: harness-mode-docs] In `README.md`, rewrite the install-finish sentence ("A confirmed finish … with `/s:doctor`.") to state that a confirmed finish runs the setup check on that terminal on one progress line, installs missing `difft`, `textual`, and the statusline without asking, and then lists only the remaining problems, each with how to fix it. Keep the headless and aborted-run sentence unchanged.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 44 | 10.6k |
| ToolSearch | 1 | 1.0k |
| Agent | 2 | 817 |
| SendMessage | 2 | 803 |
| (no tool) | 0 | 697 |
| SubagentHandback | 4 | 100 |
| **Total** | 53 | 14.1k |
