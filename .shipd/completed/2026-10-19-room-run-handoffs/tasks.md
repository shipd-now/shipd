## 1. Session driver preflight

- [x] 1.1 [req: room-run-preflight] In
      `plugins/s/skills/build/tests/test_session_driver.py` add a
      `PreflightTest` class: (a) a fake `claude` shell script (as in
      `test_a_turn_reads_the_opencode_transcript`) that writes `"$@"` one
      per line to a file in the temp dir, prints `{"session_id": "p-1",
      "result": "ok"}`, and exits 0; `session_driver.preflight(tmp,
      binary=fake)` returns `(True, None)`, and the recorded arguments
      contain `-p` and `session_driver.PREFLIGHT_PROMPT` and neither
      `--plugin-dir` nor `--resume`; (b) a fake binary printing
      `{"result": "Failed to authenticate"}` and exiting 1 returns `ok`
      False with `Failed to authenticate` in the failure; (c)
      `login_hint(k)` is non-empty for every key of `RUNNERS`, and
      `login_hint("claude") == "claude auth login"`. Run the file with
      `python3 -B -m unittest` and observe these fail.
- [x] 1.2 [req: room-run-preflight] In
      `plugins/s/skills/build/scripts/session_driver.py` add `"login":
      "claude auth login"` to the `claude` record and `"login": "opencode
      auth login"` to the `opencode` record of `RUNNERS`; add
      `PREFLIGHT_PROMPT = "Reply with the single word ok."` and
      `PREFLIGHT_TIMEOUT = 120` near `TIMEOUT_DEFAULT`; add
      `login_hint(harness)` returning `runner_for(harness)["login"]`; add
      `preflight(cwd, harness=DEFAULT_HARNESS, binary=None, effort=None,
      model_base=None, timeout=PREFLIGHT_TIMEOUT)` that calls
      `run_turn_result(PREFLIGHT_PROMPT, cwd, timeout=timeout,
      harness=harness, binary=binary, effort=effort,
      model_base=model_base)` and returns its first two elements. Name
      `preflight` in the module docstring's entry-point list. Confirm 1.1
      passes.

## 2. Room run tests

- [x] 2.1 [req: room-run-preflight, room-run-request-review, room-run-rereview]
      In `plugins/s/skills/room/tests/test_room.py`, give `FakeGh.__init__`
      a `head=None` keyword stored as `self.head`; in the `pr view` branch,
      when `"headRefOid"` is among the `--json` fields and `self.head` is
      not None, set `data["headRefOid"] = self.head`.
- [x] 2.2 [req: room-run-preflight] In
      `plugins/s/skills/room/tests/test_room_run.py` add a `FakePreflight`
      class: callable `(cwd)` recording each call and returning a scripted
      `(ok, failure)` (default `(True, None)`). Add `"preflight":
      preflight or FakePreflight()` to `RunTestBase.run_verb`'s seams (new
      `preflight=None` keyword), and add `"preflight": FakePreflight()` to
      the explicit seams of `test_default_runner_calls_run_turn_without_env`
      and `test_watch_error_ends_the_run`, so no test starts a real harness.
      Add a test: `run 7 --role reviewer --agent rev-b` with login `rev`,
      author `mikkel`, and `FakePreflight` returning `(False, "session CLI
      exited 1: Failed to authenticate: OAuth session expired")` exits 1,
      stdout is empty, stderr has one `Error:` line containing `claude auth
      login`, `gh.posts()` is empty, and the runner was never called.
- [x] 2.3 [req: room-run-request-review] In `test_room_run.py` add tests:
      (a) `run 7 --role author --agent author-a --request-review reviewer-b`
      on `FakeGh(head="abc1234def", state="MERGED")` posts the card and one
      task: parse the second post with `first_marker` and assert `task_id`
      None, `to` `reviewer-b`, `skill` `review-finding`, state
      `input-required`, metadata `head` `abc1234def`; stdout is one summary
      line; (b) with an existing `msg_comment` opened by `author-a`,
      state `input-required`, `to="reviewer-b"`, only the card is posted;
      (c) `--request-review reviewer-b` given twice opens one task; (d)
      `--role reviewer --request-review x` and `--role author --agent
      author-a --request-review author-a` each exit 2 with `gh.calls`
      empty.
- [x] 2.4 [req: room-run-rereview] In `test_room_run.py` add tests with a
      room holding `card_comment(5, "reviewer-b", role="reviewer")` and a
      finding `waiting(10, to="author-a", opener="reviewer-b")` on
      `FakeGh(head="aaa1111")`: (a) a runner hook that sets `gh.head =
      "bbb2222"` and `gh.state = "MERGED"` leads to exactly one task opened
      by the run to `reviewer-b`, skill `review-finding`, metadata `head`
      `bbb2222`; (b) the same with an existing `msg_comment` opened by
      `author-a` to `reviewer-b` whose metadata carries `head="bbb2222"`
      opens none; (c) a hook that only sets `state = "MERGED"` opens none;
      (d) a reviewer run (`--agent reviewer-b`, login `rev`, author
      `mikkel`, a task to `reviewer-b`) whose hook moves the head opens
      none; (e) a `FakeGh` wrapper failing `pr view` calls that ask for
      `headRefOid` makes the run warn on stderr, open no task, and still
      end with reason `closed`. Count posts whose `first_marker` is a
      Message with `task_id` None. Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests` and observe the new tests fail.

## 3. Room run implementation

- [x] 3.1 [req: room-run-request-review] In
      `plugins/s/skills/room/scripts/room.py` `build_parser`, add to the
      `run` subparser `--request-review` (`action="append"`, `default=[]`,
      `dest="request_review"`, `metavar="AGENT"`, help naming that it opens
      a review-finding task to that agent and needs `--role author`). Give
      `main` a `preflight=None` keyword and pass `preflight=preflight` to
      `room_run.cmd_run`.
- [x] 3.2 [req: room-run-preflight] In
      `plugins/s/skills/room/scripts/room_run.py` add `_model_base(root)`
      holding the config read now inside `_default_runner` (same
      `RoomError`), and make `_default_runner(opts, root, model_base)` use
      it. Give `cmd_run` a `preflight=None` parameter. After
      `_check_identity` and its stderr line, compute `model_base` when
      either seam is None; default `preflight` to `lambda cwd:
      session_driver.preflight(cwd, harness=opts.harness,
      effort=opts.model, model_base=model_base)`; call `preflight(root)`;
      on not ok raise `room.RoomError("harness %s is not ready: %s; sign in
      with `%s` and rerun" % (opts.harness, failure,
      session_driver.login_hint(opts.harness)))`.
- [x] 3.3 [req: room-run-request-review] In `room_run.py`, in `cmd_run`
      before `room._root`, call `parser.error` when `opts.request_review`
      is set and `opts.role != "author"`; after `_agent_name`, call
      `parser.error` when the agent is in `opts.request_review`. Add
      `_head(gh, number, repo, warned)` (runs `gh pr view <n> --json
      headRefOid --repo <repo>`; non-zero exit writes `warning: could not
      read the head of <repo>#<n>` to stderr once, tracked in the `warned`
      set, and returns `""`; a missing or non-string field returns `""`);
      `_first_to(task)` (the first message's `to`); `_has_request(tasks,
      agent, target, head=None)`; and `_open_request(gh, repo, number,
      context, agent, target, head, text, memo)` posting through
      `room._post_message(gh, repo, number, room._message(context, agent,
      text, None, metadata), room._login(gh, memo), "author")` with the
      metadata named in plan.md. After the join, when
      `opts.request_review` is set, read the room with `room._read_room`
      and the head once, then for each de-duplicated name lacking
      `_has_request` post the kick-off text from plan.md and write `room
      run: review requested from <name>` to stderr.
- [x] 3.4 [req: room-run-rereview] In `room_run.py`'s loop, when
      `opts.role == "author"`, read `before = _head(...)` just before the
      runner call; after an ok turn read `after`; when both are non-empty
      and differ, read the room, compute targets as in plan.md
      (`--request-review` names plus `card.role == "reviewer"` openers of
      tasks whose `_first_to` is this agent, minus this agent, sorted), and
      for each target lacking `_has_request(tasks, agent, target, after)`
      post the re-review text from plan.md and write `room run: re-review
      requested from <target> at <sha7>` to stderr. Confirm 2.2-2.4 pass.

## 4. Docs, version, verification

- [x] 4.1 [req: room-run-handoff-docs] In `docs/room-run.md`: in "Start the
      author", show `shipd room run 412 --role author --agent author-a
      --request-review reviewer-b` and one sentence that it opens the first
      review task once; add a section "Ask for a review by hand" with
      `shipd room message 412 --new --to reviewer-b --skill review-finding
      "Please review this pull request."`; add a section "Re-review after a
      push" stating that when an author turn moves the head, the run opens
      one re-review task per reviewer who filed a finding or was named by
      `--request-review`, once per head; in "Before you start" add that the
      run first sends one tiny probe turn and stops with one `Error:` line
      naming the sign-in command (`claude auth login`) when the harness is
      signed out, posting nothing; add a `--request-review` row to the
      flags table. Keep it under 150 lines and run `python3
      plugins/s/skills/document/scripts/docs_lint.py docs/room-run.md`
      until it exits 0.
- [x] 4.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      to one patch above the value on `main` at build time (`0.6.330` when
      planned against `0.6.329`; re-bump if a sibling landed first).
- [x] 4.3 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests` and `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests`; grep each output for `OK`/`FAILED` and
      confirm both report `OK`.
