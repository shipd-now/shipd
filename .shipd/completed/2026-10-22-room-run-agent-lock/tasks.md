## 1. Agent lock

- [x] 1.1 [req: room-run-agent-lock] In
      `plugins/s/skills/room/scripts/room_run_repo.py`, add `hold_lock`,
      `agent_lock_path`, `pr_lock_path` and `lock_pr_run` per plan.md's
      Implementation, remove `lock_state`, and make `cmd_run_repo` take the
      exclusive agent lock, plus the `<state>.lock` when it differs.
- [x] 1.2 [req: room-run-agent-lock] In
      `plugins/s/skills/room/scripts/room_run.py`, call
      `room_run_repo.lock_pr_run` after the harness preflight passes, move the
      rest of `cmd_run` into `_run_pr`, and release both handles in a
      `finally`.

## 2. Tests, docs, version

- [x] 2.1 [req: room-run-agent-lock] In
      `plugins/s/skills/room/tests/test_room_run_repo.py`, add tests: a held
      agent lock refuses repo mode with a custom `--state` (one `Error:` line
      naming the agent, the repository and the lock path, exit `1`, nothing posted, no
      runner call); a held shared agent lock also refuses repo mode.
- [x] 2.2 [req: room-run-agent-lock] In
      `plugins/s/skills/room/tests/test_room_run.py`, add tests: a held
      exclusive agent lock refuses a PR run before it joins; a held PR lock
      for PR 7 refuses a PR run on 7; a held PR lock for PR 8 does not refuse
      a PR run on 7.
- [x] 2.3 [req: room-run-agent-lock] In `docs/room-run.md`, say that one
      agent runs once per repository, keeping the doc within 150 lines; run
      `docs_lint.py` on it. Bump `plugins/s/.claude-plugin/plugin.json` from
      `0.6.343` to `0.6.344`.

## 3. Verify

- [x] 3.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests` and grep the output for `OK`/`FAILED`.
