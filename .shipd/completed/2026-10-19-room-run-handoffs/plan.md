# room-run-handoffs
Status: verified
Planned-at: 1b18fd04f5ef97aa08a89369171542c041f4c0a9
Gated-hash: ccbf695980ea

## Idea

Teach `shipd room run` the three hand-offs its first live test needed: a
harness sign-in preflight before join, a `--request-review` kick-off, and a
re-review task after an author turn moves the PR head.

### Motivation

On unkannybanny PR 23 a human had to open the first review task and, after the
author's fix push dismissed the approval, the re-review task too, or the PR
sat BLOCKED. The reviewer's run also joined and claimed a task before its
expired harness sign-in failed the turn.

### Details

- `plugins/s/skills/build/scripts/session_driver.py`: each RUNNERS record
  gains a `login` hint; new `preflight()` runs one minimal probe turn.
- `plugins/s/skills/room/scripts/room_run.py`: preflight before join; the
  `--request-review` kick-off after join; the re-review after a head-moving
  author turn.
- `plugins/s/skills/room/scripts/room.py`: the `--request-review` flag and a
  `preflight` seam on `main`.
- Tests: `plugins/s/skills/room/tests/test_room_run.py`,
  `plugins/s/skills/room/tests/test_room.py` (FakeGh head),
  `plugins/s/skills/build/tests/test_session_driver.py`.
- `docs/room-run.md`; `plugins/s/.claude-plugin/plugin.json` version bump.

Affected capabilities: `room-runner` (modified, requirements added).

### Non-goals

- No change to the `/s:room` skill, its harness body, or its reference; an
  interactive author opens a re-review by hand with `message --new`.
- No new room verb, no change to `watch`, `message`, or the room schema.
- No `--no-preflight` flag and no retry of a failed preflight.
- `docs/pr-room.md` (at its 150-line cap) is not edited.

## Implementation

- **Preflight (Q4).** `session_driver.PREFLIGHT_PROMPT = "Reply with the
  single word ok."`, `PREFLIGHT_TIMEOUT = 120`. `preflight(cwd,
  harness=DEFAULT_HARNESS, binary=None, effort=None, model_base=None,
  timeout=PREFLIGHT_TIMEOUT) -> (ok, failure)` calls `run_turn_result` with
  that prompt, no resume, no `plugin_dir`, no `extra_args`, and returns its
  first two elements. Records gain `"login": "claude auth login"` and
  `"login": "opencode auth login"`; `login_hint(harness)` returns
  `runner_for(harness)["login"]`. Rejected: an auth-status read, which may
  still report signed in for an expired OAuth token.
- **Run seam.** `room.main(..., runner=None, preflight=None)` passes
  `preflight` to `room_run.cmd_run(opts, parser, gh, runner, sleep, clock,
  preflight=None)`. The seam is `preflight(cwd) -> (ok, failure)`. A new
  `_model_base(root)` holds the config read `_default_runner` does today
  (same `RoomError`); both default seams use it. The default preflight calls
  `session_driver.preflight(root, harness=opts.harness, effort=opts.model,
  model_base=...)`. It runs after `_check_identity` and before the url read
  and join; on not ok, `cmd_run` raises `room.RoomError("harness <h> is not
  ready: <failure>; sign in with `<login_hint>` and rerun")` — one `Error:`
  line, exit 1, empty stdout, nothing posted.
- **Kick-off flag (Q3).** `run` gains `--request-review AGENT`
  (`action="append"`, default `[]`, dest `request_review`). With a role other
  than `author`, or naming the run's own agent, it is `parser.error` (exit 2)
  before any gh call. After join, the run reads the room and the head once;
  for each named agent, in order, de-duplicated, it opens a request unless a
  task already exists whose opener is this agent and whose first message's
  `to` is that agent.
- **Head read.** `_head(gh, number, repo)` runs `gh pr view <n> --json
  headRefOid --repo <repo>`; a non-zero exit warns once on stderr and yields
  `""`, as does a missing field. A head read never fails the run.
- **Request post.** `_open_request(gh, repo, number, context, agent,
  reviewer, head, text, memo)` posts `room._message(context, agent, text,
  None, metadata)` through `room._post_message` with the login from
  `room._login(gh, memo)` and role `author`. Metadata: `state`
  `input-required`, `round` 1, `to` the reviewer, `skill` `review-finding`,
  plus `head` (the full SHA) when known. It writes nothing on stdout.
  Kick-off text: `Please review this pull request at head <sha7>. Post each
  finding as a task to <agent>; approve when nothing blocking is left.`
  (`at head <sha7>` dropped when the head is unknown). Re-review text:
  `Re-review please: the head moved to <sha7>. Approve it if nothing blocking
  remains, or post each finding as a task to <agent>.` Stderr: `room run:
  review requested from <r>` and `room run: re-review requested from <r> at
  <sha7>`.
- **Re-review (Q1, Q2).** With role `author`, the run reads the head before
  each turn and again after an ok turn. When both reads are non-empty and
  differ, it reads the room and computes targets: the `--request-review`
  agents plus every agent whose card role is `reviewer` and who opened a task
  whose first message's `to` is this agent, minus this agent, sorted. It
  opens a re-review for each target unless a task exists whose opener is this
  agent, whose first message's `to` is the target, and whose first message's
  `head` metadata equals the new head. Not run after a failed turn. Rejected:
  a skill step (model-dependent, untested) and a new verb (extra surface).
- **Stdout.** Unchanged: the summary line only; its keys are unchanged.

Risk: the in-turn `/s:room` ends only after its 540 s empty wait, so a
re-review posts up to nine minutes after the push. Risk: the probe spends one
small model call per run.

## Questions and answers

### Q1: Where the post-push re-review hand-back lives
- **Question:** Options: (1) `room run` compares the head before and after
  each author turn and opens the task, idempotent per head; (2) the `/s:room`
  author path runs `message --new`; (3) a new `room rereview` verb used by
  both. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It is deterministic, tested with FakeGh, idempotent
  through the `head` metadata key, and leaves the skill unchanged.
- **Queued:** q-rereview-handback-location

### Q2: Which agents get the re-review task
- **Question:** Options: (1) the `--request-review` agents plus reviewer-role
  agents who opened a task to this author; (2) only those reviewers; (3)
  every reviewer card. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It covers a reviewer who approved with no findings,
  whose approval a last-push rule still dismisses, and pings no unrelated
  reviewer.
- **Queued:** q-room-run-rereview-targets

### Q3: How the first review is requested
- **Question:** Options: (1) a repeatable author-only `--request-review
  <agent>` flag, plus the manual `message --new` step in the how-to; (2) the
  how-to only; (3) wait for a reviewer card and address it. Recommendation:
  (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. An addressed task waits in the backlog, so no
  reviewer card is needed first, and the run never guesses the addressee.

### Q4: What the harness preflight runs
- **Question:** Options: (1) one minimal probe turn through the runner's own
  argv, with a `login` hint per RUNNERS record; (2) a per-record auth-status
  command; (3) both. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It exercises the path that failed on PR 23, where a
  local status read may still report signed in.

## Readiness attestation

### Problem and motivation

Two unattended runs could not finish PR 23 without a human opening two tasks,
and a signed-out harness failed only after the run joined and claimed a task.

Evidence:

- PR 23 issue comments: the kick-off 6259256645 and re-review 6259945168 were
  opened by hand; reviewer approval 6259602096 preceded the fix pushes.
- `plugins/s/skills/room/scripts/room_run.py:123-139` joins, then loops; no
  task is ever opened and no preflight runs.

### Scope and non-goals

The run, the session driver, their tests, one how-to, and the version; the
skill, watch, schema, and `docs/pr-room.md` stay untouched.

Evidence:

- `docs/pr-room.md` is 150 lines, the how-to cap in
  `plugins/s/skills/document/scripts/docs_lint.py:48`.
- `room_schema.message_from_dict` keeps unknown metadata keys, so `head`
  needs no schema change (`room_schema.py:281-311`).

### Affected capabilities and files

One capability and eight files.

Evidence:

- Capability `room-runner`; files `session_driver.py:203-216`,
  `room_run.py:38-190`, `room.py:1055-1110`, `test_room_run.py:53-60`,
  `test_room.py:164-176`, `test_session_driver.py`, `docs/room-run.md`,
  `plugin.json`.
- Runnable premise: `claude auth --help` → exit 0, lists `login`.
- Runnable premise: `_claude_argv('claude', PROMPT, None, None, None, None,
  None)` → `claude -p PROMPT --output-format json --permission-mode
  bypassPermissions`, no plugin dir or resume.
- Runnable premise: room suite → 247 tests OK; `docs_lint.py
  docs/room-run.md` → exit 0.

### No open task-shaping decision

Every decision is settled by the planner pending human review.

Evidence:

- Re-review placement Q1, targets Q2, kick-off Q3, preflight Q4: planner
  defaults after INSUFFICIENT oracle verdicts.
- Head-read failure handling and request texts: investigation (PR 23's
  manual texts, `_pr_author`'s soft-fail pattern).
