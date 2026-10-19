## 1. Failing tests

- [x] 1.1 [req: room-run-start, room-run-loop, room-run-stop] Add
      `plugins/s/skills/room/tests/test_room_run.py`. Import `FakeGh`,
      `_run`, `card_comment`, `msg_comment`, `RoomTestBase`, `FakeClock`,
      `FakeSleep` from `test_room` (same directory). Add a `FakeRunner`
      class: callable `(prompt, cwd, resume_id, turn_index)` recording each
      call plus `os.environ.get("SHIPD_ROOM_AGENT")`, returning a scripted
      `(ok, failure, session_id)` and optionally running a hook that mutates
      the `FakeGh` (e.g. posts the agent's `completed` reply, opens a second
      task, or sets `state = "MERGED"`). Drive every test through
      `_run(argv + ["--root", self.root], gh, env=..., seams={"sleep": ...,
      "clock": ..., "runner": FakeRunner(...)})`. Cover every scenario in
      the change's `room-runner` delta spec except the two in `room-run-tests-docs`:
      reviewer-as-author refusal (no POST, runner not called); one card
      posted with role `reviewer` and the three default skills; unknown
      harness exits `2` with no gh call; two tasks resume one session
      (resume ids `None` then `s-1`, prompt prefix `/s:room
      https://github.com/o/r/pull/7 role author`, `turns` 2); runner sees
      `SHIPD_ROOM_AGENT` `rev-b`; no task → budget elapses, `turns` 0, reason
      `budget`; merged PR → reason `closed`, `closed` `merged`, exit 0;
      `--max-turns 1` → reason `turn-cap`; failed turn → reason `turn-failed`,
      `failure` set, one `Error:` line, exit 1. Also assert stdout holds
      exactly one line in every non-usage test, and that the default runner
      calls `session_driver.run_turn` with no `env` keyword (patch
      `room_run.session_driver.run_turn` with a `Mock` returning `(True,
      None, "s-1")`). Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests` and observe the new tests fail.

## 2. The run verb

- [x] 2.1 [req: room-run-start] In `plugins/s/skills/room/scripts/room.py`
      `build_parser`, add the `run` subparser (parents `[common]`) with the
      flags listed in `plan.md` "Flags", `--role` required with choices
      `room_schema.ROLE_VALUES`, help `join once, then answer each task with a
      headless /s:room turn`; `set_defaults(func=None)`. Change `main` to
      `main(argv=None, gh=None, sleep=time.sleep, clock=time.monotonic,
      runner=None)` and, for verb `run`, do a function-local `import
      room_run` and return `room_run.cmd_run(opts, verbs["run"], gh, runner,
      sleep, clock)` inside the existing `try`. Validate the harness at the
      top of `cmd_run` with `session_driver.runner_for`, turning
      `UnknownHarnessError` into `parser.error`. Update the module docstring's
      verb list. In `plugins/s/skills/room/tests/test_room.py:497` add
      `room_run` to the `allowed` set (keep the `assertIn` loop over the
      three original names only).
- [x] 2.2 [req: room-run-start] Create
      `plugins/s/skills/room/scripts/room_run.py` (stdlib plus `room`,
      `session_driver`, `spec_common`, `cli_common`; same `sys.path` setup as
      `room.py`). Implement the start of `cmd_run` per `plan.md`
      "Reuse, not refactor": resolve root/agent/room, read login and author,
      apply the Q2 rules (Error text for the author case copied from
      `room.cmd_whoami`), write `room run: acting as @<login> (<source>)` to
      stderr, read the PR url, then join through `room.cmd_join` with a
      Namespace and captured stdout. Default skills
      `("review-finding", "question", "status")` when `opts.skill` is empty.
- [x] 2.3 [req: room-run-loop] In `room_run.py`, add `_default_runner(opts,
      root)` returning the `session_driver.run_turn` wrapper from `plan.md`
      "Turn runner seam" (plugin dir = `os.path.normpath(os.path.join(HERE,
      "..", "..", ".."))`), and the loop: budget check, `room.cmd_watch` with a
      Namespace and captured stdout, parse lines, the turn call with the
      Q1 prompt, `os.environ[room.AGENT_ENV] = agent` before the first turn,
      session id carry-over, cursor from the last surfaced line.
- [x] 2.4 [req: room-run-stop] In `room_run.py`, implement the stop reasons,
      the summary line, and exit codes exactly as `room-run-stop` states;
      catch `room.RoomError` from the watch as `watch-failed`; print the
      `Error:` line with `cli_common.err`. Run the room suite until 1.1
      passes.

## 3. Surfaces and docs

- [x] 3.1 [req: room-run-tests-docs] In `plugins/s/bin/shipd:187` change the
      `room` banner line to end `close, watch, whoami, run`.
- [x] 3.2 [req: room-run-tests-docs] Write `docs/room-run.md` under
      `/s:document`'s standard as a `how-to` titled `# Run two agents on a
      pull request unattended`: what `room run` does and that it spends
      tokens only when a task arrives; before you start (link
      `agent-identity.md`, two accounts, an open PR); terminal 1 — the author
      in the PR worktree on the default login, `shipd room run 412 --role
      author --agent author-a`; terminal 2 — `GH_CONFIG_DIR=~/.config/gh-reviewer
      shipd room run 412 --role reviewer --agent reviewer-b`; the flags
      `--max-turns`, `--budget`, `--harness`, `--model`; the summary line and
      each `reason`; that turns run with `bypassPermissions`; see also
      `pr-room.md`, `room-wake-reference.md`, `multi-agent-pr.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/room-run.md`
      until it exits 0.
- [x] 3.3 [req: room-run-tests-docs] In `docs/pr-room.md` "See also" add a
      bullet linking `room-run.md`; in `docs/room-wake-reference.md` "Known
      limits", end the "Replies wake no other workflow" bullet with a
      sentence that `shipd room run` keeps two local agents talking without
      the wake, linking `room-run.md`. Re-run `docs_lint.py` on both; each
      exits 0.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      to one patch above the value on `main` at build time (`0.6.329` when
      planned; re-bump if a sibling landed first).
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests`; grep the output for `OK`/`FAILED` and
      confirm both report `OK`.
