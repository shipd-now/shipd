# room-run
Status: verified
Planned-at: 139a656339c9fc8d20837fd0603da4cb04c8d128
Gated-hash: fcf5af20efe9

## Idea

Add `shipd room run <pr>`: a local loop that joins this agent's card once,
waits with `watch` (no LLM), and runs one resumed headless `/s:room` turn per
task addressed to it, until the PR closes or a cap is hit.

### Motivation

Two agents on separate GitHub accounts cannot hold a PR-room conversation
unattended: the Actions wake never wakes another workflow from its own
replies, and `/s:room` needs a person to start every turn. A user who wants an
author and a reviewer to talk a PR through without CI has no way to do it.

### Details

- New verb `run` in `plugins/s/skills/room/scripts/room.py`, logic in a new
  sibling `room_run.py` (imported lazily for `run` only).
- Identity check at start, card join once, then watch → turn → watch.
- One JSON summary line; exit codes per stop reason.
- Tests in `plugins/s/skills/room/tests/test_room_run.py`; banner line in
  `plugins/s/bin/shipd`; new how-to `docs/room-run.md`; links from
  `docs/pr-room.md` and `docs/room-wake-reference.md`; version bump.

Affected capabilities: `room-runner` (new). Unchanged: `pr-room`,
`room-acting-account`, `shipd-room`.

### Non-goals

- No change to the `/s:room` skill, its harness body, or `watch` itself.
- No `env` override, token flag, or account config: the account stays the
  process environment's.
- `room_run.py` is not added to the Actions wake bundle; `docs/multi-agent-pr.md`
  (at its 100-line cap) is not edited.
- No retry of a failed turn and no posting by the runner itself.

## Implementation

- **Module split.** `room.py` registers the `run` subparser (so `shipd room
  --help` lists it) and in `main`, for verb `run` only, does a function-local
  `import room_run` and returns `room_run.cmd_run(opts, parser, gh, runner,
  sleep, clock)`. `main` gains `runner=None`. Rationale: the wake bundles
  `room.py` without `session_driver`, so a top-level import would break the
  CI copy. `test_module_imports_only_stdlib_and_named_siblings` adds
  `room_run` to its allowed set. `room_run.py` imports `room`,
  `session_driver`, `spec_common`, `cli_common`. Rejected: everything in
  `room.py` (breaks the bundle and the allow-list).
- **Reuse, not refactor.** Join calls `room.cmd_join` with an
  `argparse.Namespace` (`pr, agent, root, repo, skill, description, harness,
  role, max_rounds`) and stdout redirected to a `StringIO`. Each wait calls
  `room.cmd_watch(ns, gh, sleep, clock, parser)` with `since=cursor`,
  `interval`, `timeout=remaining budget`, `once=False`, stdout captured;
  lines are parsed as JSON, a `closed` key marks the closed line. Identity
  uses `room._login`, `room._pr_author`, `room._credential_source`; the
  refusal text matches `cmd_whoami`'s. PR url: `room._gh_json(gh, ["pr",
  "view", str(number), "--json", "url", "--repo", repo])`.
- **Prompt.** `/s:room <url> role <role>, skills <s1>, <s2>, ...` — the skill
  rejoins every turn and honors a named role and skill list (Q1).
- **Turn runner seam.** `runner(prompt, cwd, resume_id, turn_index) -> (ok,
  failure, session_id)`, `session_driver.drive`'s contract. Default wraps
  `session_driver.run_turn(prompt, cwd, resume_id=..., timeout=turn_timeout,
  harness=..., effort=opts.model, model_base=spec_common.resolve_model_base(
  spec_common.resolve_config(root)[0]), plugin_dir=<plugins/s>)`. A new
  session id replaces the held one; `None` keeps it.
- **Env.** `os.environ["SHIPD_ROOM_AGENT"] = agent` before the first turn;
  nothing passes `env=`, so `GH_TOKEN`/`GH_CONFIG_DIR` reach `gh` and the
  harness.
- **Flags.** `--role` required (choices `room_schema.ROLE_VALUES`), `--skill`
  repeatable, `--description`, `--harness` (default
  `session_driver.DEFAULT_HARNESS`), `--model` (model id or effort level,
  default none), `--max-turns` (positive int, 10), `--budget` (seconds, >0,
  14400), `--turn-timeout` (seconds, `session_driver.TIMEOUT_DEFAULT`),
  `--interval` (30), `--since` (`room._cursor`, `0:0`), plus the common flags.
- **Stdout.** Only the summary; progress goes to stderr (`room run: turn <n>
  on task(s) <ids>`).

Risk: the in-turn `/s:room` waits up to 540 s before ending, so a turn takes
wall time without tokens; `--turn-timeout` 1800 s covers it. Risk: the turn
runs with `bypassPermissions` (as autopilot's do); the doc says so.

## Questions and answers

### Q1: How does a headless turn keep the card's role and skills?
- **Question:** Options: (1) the prompt names role and skills; (2) bare
  `/s:room <pr>`, role cleared on rejoin; (3) change the skill to skip rejoin.
  Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1: the skill passes a named role and skill list on every
  join, and a rejoin without `--role` clears it.
- **Cited:** plugins/s/skills/room/SKILL.md, completed room-speaker-identity Q4

### Q2: Role and identity handling at start
- **Question:** Options: (1) `--role` required; reviewer/ci refused as the PR
  author or on an unreadable login/author; author needs a readable login and
  warns when not the PR author; (2) `--role` optional, check only when given;
  (3) author also refused when not the PR author. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1.
- **Queued:** q-room-run-role-identity

### Q3: Default run bounds
- **Question:** Options: (1) `--max-turns` 10, `--budget` 14400 s, turn
  timeout 1800 s; (2) 6 turns, 2 h; (3) no wall-clock default.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1.
- **Queued:** q-room-run-default-bounds

### Q4: Exit codes per stop reason
- **Question:** Options: (1) 0 for closed, turn-cap, budget; 1 plus an
  `Error:` line for turn-failed, watch-failed; (2) 0 only for closed; (3)
  always 0. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1.
- **Queued:** q-room-run-exit-codes

### Q5: Where the two-terminal docs live
- **Question:** Options: (1) new how-to `docs/room-run.md` linked from
  `pr-room.md` and the wake limit; (2) a section in `pr-room.md`; (3) extend
  `multi-agent-pr.md`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1.
- **Queued:** q-room-run-setup-docs-placement

### Q6: What may an unattended room turn do?
- **Question:** Options: (1) restricted per role (reviewer reads, tests, room verbs; author also edits and pushes its branch); (2) full `bypassPermissions`, as autopilot's turns; (3) accept-edits with an allowlisted shell.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. The user restricts each agent through its GitHub account, so turns keep session_driver's existing `bypassPermissions`; the how-to states this.

## Readiness attestation

### Problem and motivation

No path lets two account-separated agents converse on a PR unattended.

Evidence:

- `docs/room-wake-reference.md` "Replies wake no other workflow".
- `plugins/s/skills/room/SKILL.md` "When to stop": a turn ends on an empty wait.

### Scope and non-goals

A new verb and docs; skill, watch, and wake bundle untouched.

Evidence:

- `room.py:851` `cmd_watch` and `room.py:580` `cmd_join` reused as-is.
- Wake bundle list `plugins/s/bin/shipd:2033`; `docs/multi-agent-pr.md` is 100 lines.

### Affected capabilities and files

One new capability and nine files.

Evidence:

- Capability `room-runner` (new). Files: `room.py`, new `room_run.py`,
  `tests/test_room_run.py`, `tests/test_room.py:497`, `plugins/s/bin/shipd:187`,
  `docs/room-run.md`, `docs/pr-room.md`, `docs/room-wake-reference.md`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `shipd room --help` → exit 0, verbs join list whoami
  message close watch.
- Runnable premise: `_claude_argv('claude','/s:room 7','sid-1',
  'claude-sonnet-4-5',None,'/p',None)` → `... --model claude-sonnet-4-5
  --resume sid-1`; opencode with `high` and base `anthropic/x` →
  `--model anthropic/x#high --session ses_1 /shipd-room 7`; `runner_for('nope')`
  raises `UnknownHarnessError`.
- Runnable premise: `docs_lint.py` on the four room docs → exit 0 each.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Prompt carries role/skills: oracle, Q1. Role/identity, bounds, exit codes,
  docs placement: planner defaults, Q2-Q5.
- Module split and lazy import: investigation (allow-list test, wake bundle).
- Default skills: investigation (the skill's default card).
