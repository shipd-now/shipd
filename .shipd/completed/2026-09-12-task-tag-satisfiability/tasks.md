## 1. The readiness mirror and its parity guard

- [x] 1.1 [P1] [req: task-group-satisfiability] In `plugins/s/skills/build/tests/test_spec_lint.py`, add tests for a readiness helper that, given a tasks file's parsed checkbox states and group tags, returns the set of currently-ready pending task ordinals: a barrier is ready only when every task before it in file order is done; a grouped task only when every barrier before it is done and every task in a strictly-lower-numbered group anywhere in the file is done. Cover the barrier idiom, fully-grouped monotonic, fully sequential, and the cycle shape. Run them and observe them fail — the helper does not exist yet.
- [x] 1.2 [P2] [req: task-group-satisfiability] In `plugins/s/skills/build/scripts/spec_lint.py`, implement that readiness helper as a pure function over parsed task state, mirroring the `ready()` rule in `plugins/s/skills/build/scripts/claim_task.sh`'s `first_ready_line` awk. Keep it stdlib-only and side-effect free. Confirm the tests from task 1.1 pass.
- [x] 1.3 [P3] [req: task-group-satisfiability] In `plugins/s/skills/build/tests/test_claim_task.py`, add a differential parity test: for each configuration in a corpus covering every combination the rule distinguishes — barrier present or absent, group numbers monotonic or not, and some tasks already done — write a real tasks file, ask the coordinator via `claim_task.sh next` what it considers ready, and assert the linter's helper reports the same ready task. Include the cycle shape, where both must report nothing ready.

## 2. The satisfiability check

- [x] 2.1 [P4] [req: task-group-satisfiability] In `plugins/s/skills/build/tests/test_spec_lint.py`, add tests for the check itself: the cycle shape produces an error naming the unreachable tasks by checkbox ordinal and a non-zero exit; the barrier idiom, monotonic grouping, and a fully sequential file each produce no satisfiability finding; a file whose earlier tasks are already done but whose remaining pending tasks form a cycle is still refused; and a change with no `tasks.md` is a no-op. Run them and observe them fail.
- [x] 2.2 [P5] [req: task-group-satisfiability] In `plugins/s/skills/build/scripts/spec_lint.py`, implement the check beside `check_task_traceability`: drain the tasks file by repeatedly marking every ready pending task done using the helper from task 1.2 until no further task becomes ready, then report every still-pending task as an error naming its checkbox ordinal. Register it with the other task checks so it runs on every change lint. Confirm the tests from task 2.1 pass.

## 3. The authoring guidance

- [x] 3.1 [P6] [req: parallel-task-group-format] In `plugins/s/skills/build/tests/test_subagent_contract.py` (or whichever module already guards the build skill's prose, matching where the existing coordinator-reference assertions live), add a test asserting the build skill's task-authoring guidance names both safe idioms — a fully untagged file, or group numbers that never decrease down the file — and no longer calls an untagged task unconditionally safe. Run it and observe it fail.
- [x] 3.2 [P7] [req: parallel-task-group-format] In `plugins/s/skills/build/SKILL.md`, replace the Phase 2 sentence advising "When in doubt, leave a task untagged (a safe barrier)" with the two safe idioms, stating why an untagged task is safe only where no groups surround it: a barrier orders by file position while a group orders by number, so a barrier between a higher-numbered group and a lower-numbered one makes both unreachable. Confirm the test from task 3.1 passes.

## 4. Ship

- [x] 4.1 [P8] [req: *] Bump the version in `plugins/s/.claude-plugin/plugin.json` from `0.6.209` to `0.6.210`.
- [x] 4.2 [P9] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and confirm the whole engine suite passes with the new tests included.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 134 | 59.6k |
| Edit | 14 | 10.1k |
| Read | 18 | 4.3k |
| (no tool) | 0 | 3.3k |
| Agent | 2 | 1.8k |
| ToolSearch | 2 | 275 |
| **Total** | 170 | 79.3k |
