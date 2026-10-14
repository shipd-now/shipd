## 1. Precondition and version

- [x] 1.1 [req: room-watch-tests] Merge `main` into the change branch after
      `room-schema` and `room-cli-verb` have merged; confirm
      `plugins/s/skills/room/scripts/room.py` defines `main`, `_default_gh`,
      `_resolve_room`, `_read_room`, `_post`, `_agent_name`, `_max_rounds`,
      and `RoomError`, and that `room_schema` exposes `build_tasks`,
      `next_round`, `at_round_cap`, `Message`, `render_comment`,
      `parse_comment`. Stop and report if any symbol is missing.
- [x] 1.2 [req: room-watch-tests] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to one patch above the value
      `main` carries.
- [x] 1.3 [req: room-watch-tests] In `plugins/s/bin/shipd`, change the `room`
      banner line's verb list to `join, list, message, close, watch`; in
      `plugins/s/skills/build/tests/test_shipd_cli.py` add a test that
      `shipd --help` stdout contains `close, watch`.

## 2. Predicate

- [x] 2.1 [req: room-actionable-predicate] In
      `plugins/s/skills/room/tests/test_room.py` add a `_task(**kw)` helper
      building a `room_schema.Task` and an `ActionableTest` class: addressed
      task is actionable for `claude-b` only; unaddressed task with skill
      `review-finding` is actionable only when `skills` holds it; a task
      whose `last_agent` is the watcher is not actionable; tasks at
      `completed`, `failed`, `canceled`, `working`, `submitted` yield an
      empty `actionable_tasks`; results are ordered by `id`. Run it and
      observe the AttributeError.
- [x] 2.2 [req: room-actionable-predicate] In `room.py` add
      `is_actionable(task, agent, skills=())` and
      `actionable_tasks(tasks, agent, skills=())` per the plan's predicate
      decision, with a docstring naming `room-action-wake` as an importer.
      Run the 2.1 tests until they pass.

## 3. Room read split

- [x] 3.0a [req: room-gh-seam] In `plugins/s/skills/room/tests/test_room.py`
      add a test: `FakeGh` seeded with a review comment id `900`
      (`created_at` `2026-01-01T10:00:00Z`) opening a task and an issue
      comment id `50` (`created_at` `2026-01-01T10:05:00Z`) replying to it
      makes `list --json` report one task holding both messages with the
      reply last. Run it and observe it fail (id order puts `50` first).
- [x] 3.0b [req: room-gh-seam] In `plugins/s/skills/room/scripts/room.py`
      sort the union in `_read_room` by `(created_at, id)` instead of `id`,
      parsing `created_at` as an ISO-8601 string (lexicographic order is
      chronological for GitHub's `Z`-suffixed stamps). Run the 3.0a test and
      the room suite until they pass.
- [x] 3.1 [req: room-watch-verb] In `test_room.py` add tests:
      `room._read_comments(gh, "o/r", 7)` returns the flattened comment
      dicts of two slurped pages in order; `room._room_from_comments(comments)`
      returns the same `(cards, tasks)` that `_read_room` returns for them;
      `room._last_comment(comments, task)` returns the comment whose id is
      the task's last reply, or the opener when the task has one message.
- [x] 3.2 [req: room-watch-verb] In `room.py` extract the paginated fetch
      from `_read_room` into `_read_comments(gh, repo, number)`, move the
      parse/warn/`build_tasks` body into `_room_from_comments(comments)`, make
      `_read_room` compose the two with an unchanged return value, and add
      `_last_comment(comments, task)`. Run the 3.1 tests and the existing
      room suite until both pass.

## 4. Watch loop

- [x] 4.1 [req: room-watch-verb, room-watch-exit] In `test_room.py` add a
      `_watch(argv, gh, sleep=None, clock=None)` helper around
      `room.main([...], gh=gh, sleep=..., clock=...)` capturing stdout and
      stderr, a `FakeClock` whose each call advances by a given step, and
      a `FakeSleep` recording its arguments and running an optional
      per-call callback. Add tests: first poll on a PR with a task to
      `claude-b` and one to `codex-a` prints one line (`task`, `comment`,
      `text`, `url`, `context`, `cursor` keys; `cursor` is the
      `<issue>:<review>` pair of max ids) and exits 0 after one room read;
      `--since <cursor> --once` with the task's endpoint component at its
      last comment id prints nothing; a review-comment task whose id is below
      the issue component is still surfaced when the review component is
      lower than it; no card plus an unaddressed `review-finding`
      task prints nothing and no `Error:`; a `FakeSleep` callback that
      appends a task on its second call yields two empty polls, then the
      task, with `sleep` called twice with `30.0`; `--once` with nothing
      prints the `watch: no actionable task on o/r#7 (cursor <n>)` stderr
      line with empty stdout and exits 0; `--timeout 60 --interval 20` with
      a clock stepping 25 s and no task exits 0 with empty stdout after the
      expected number of polls; a failing
      comments read exits 1 with one `Error:` line and no sleep;
      `--interval 0` exits 2; a `gh` raising `KeyboardInterrupt` exits 130
      with nothing on stderr but no traceback.
- [x] 4.2 [req: room-watch-verb, room-watch-exit] In `room.py` add the
      `watch` subparser (`pr`, `--since` str default `0:0` parsed into an
      `(issue, review)` int pair with a bare integer as the issue component,
      `--interval` float
      default 30.0, `--timeout` float default None, `--once`; `--agent`,
      `--root`, `--max-rounds` from the shared parent), extend `main` to
      `main(argv=None, gh=None, sleep=time.sleep, clock=time.monotonic)`,
      and implement `cmd_watch(opts, gh, sleep, clock, parser)`: validate
      the interval, resolve the room and agent, then loop per the plan's
      "Loop and seams" decision, emitting lines with `_watch_line(task,
      comment, context, cursor)`. Catch `KeyboardInterrupt` in `main` →
      return 130. Run the 4.1 tests until they pass.

## 5. Round cap

- [x] 5.1 [req: room-watch-round-cap] In `test_room.py` add tests: as
      `claude-b` with a card, `--once --max-rounds 6` on a task to
      `claude-b` at round 6 (last agent `codex-a`) records exactly one POST
      whose marker holds `taskId` of the task and `metadata`
      `{"reason":"round-cap","round":7,"state":"failed"}`, text `round cap
      (6) reached`, stderr holds `task <id>: round cap reached — posted
      failed (round-cap)`, stdout is empty, exit 0; the same without a card
      posts nothing and prints the `WARNING: task <id>: round cap reached;
      join the room to close it` line; a second actionable task below the
      cap in the same poll is still printed and the exit is 0.
- [x] 5.2 [req: room-watch-round-cap] In `cmd_watch` apply
      `room_schema.at_round_cap(task, agent, max_rounds)` to each actionable
      task before the cursor filter: post via `_post` with a `Message`
      rendered by `room_schema.render_comment` when the watcher has a card,
      else `cli_common.warn`; exclude the task from the surfaced set. Run the
      5.1 tests until they pass.

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`; grep each output for `OK` (not the
      tail). Run `python3 plugins/s/skills/build/scripts/version_guard.py
      --base main --head HEAD` and `python3
      plugins/s/skills/build/scripts/spec_lint.py room-watch`; all exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 108 | 2.7k |
| Agent | 8 | 1.2k |
| (no tool) | 0 | 1.2k |
| SubagentHandback | 10 | 149 |
| Skill | 1 | 3 |
| **Total** | 127 | 5.3k |
