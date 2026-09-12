# tasks

- [x] 1.1 [P1] [req: task-group-satisfiability] Add failing tests to `plugins/s/skills/build/tests/` covering both new scenarios: a sound `[P1]`/`[P2]`/barrier tasks file whose `[P1]` task is `[x]` and `[P2]` task is `[~]` must report no satisfiability finding, and a broken `[P3]`/barrier/`[P2]` file whose tasks are all `[x]` must still report one naming the unreachable tasks
- [x] 2.1 [P2] [req: task-group-satisfiability] In `plugins/s/skills/build/scripts/spec_lint.py`, make `check_task_satisfiability` normalize every task to pending before its drain — build the working list as `[(" ", group) for _state, group in states]` — and update its docstring to say the check reads the group configuration alone, independently of checkbox state. Do not modify `ready_task_ordinals`, which mirrors the coordinator's runtime rule and is pinned to it by an existing test
- [x] 3.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` from the repo root and confirm the whole build suite passes, including the existing test that pins the linter's readiness rule to the coordinator's
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.211` to `0.6.212` — AGENTS.md requires every change touching `plugins/s/` to bump the plugin version in the same PR

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 65 | 22.2k |
| (no tool) | 0 | 1.3k |
| Agent | 2 | 1.1k |
| AskUserQuestion | 1 | 694 |
| Edit | 4 | 45 |
| **Total** | 72 | 25.3k |
