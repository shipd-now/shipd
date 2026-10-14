# room-watch
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Add `shipd room watch <pr> [--since CURSOR] [--interval S] [--timeout S]
[--once]`: a foreground poll that prints one NDJSON line per newly actionable
task for this agent, enforces the round cap, and exits on a task, on
`--once`, or on `--timeout`.

### Motivation

Once `room-cli-verb` lands, an agent can post and read room comments but
cannot learn when it is its turn, so the `/s:room` skill and the CI wake
cannot wait on a task without re-implementing the actionable rule. This is
the epic's first wake path and the predicate `room-action-wake` imports.

### Details

- `plugins/s/skills/room/scripts/room.py` gains the `watch` subparser,
  `cmd_watch`, the pure `is_actionable` / `actionable_tasks` functions, and
  a `_read_comments` / `_room_from_comments` split of the room read.
- `plugins/s/skills/room/tests/test_room.py` gains the watch tests over the
  existing `FakeGh`, with injected `sleep` and `clock`.
- `plugins/s/bin/shipd`'s `room` banner line names `watch`; the plugin
  version advances one patch above `main`'s value at build time.

Affected capabilities: `pr-room` (modified — `room-schema` adds it). Depends
on `room-schema` and `room-cli-verb` merging first: this plan binds to their
APIs as given and re-specifies none of their requirements. No new `room`
config member is needed.

### Non-goals

- No `/s:room` skill, harness body, or docs beyond the banner (`room-skill`).
- No workflow template or CI guard step (`room-action-wake` imports
  `is_actionable`; it is not written here).
- No change to `review_gate.py`, `room_schema.py`, `spec_common.py`, or the
  `join`/`list`/`message`/`close` contracts.
- No background mode, daemon, webhook, or API `since` timestamp filter.

## Implementation

- **Predicate is a module-level pure function.** `is_actionable(task, agent,
  skills=())` is true exactly when `task.state == "input-required"`,
  `task.last_agent != agent`, and either `task.to == agent` or `task.to` is
  `None` and `task.skill in skills`; terminal states fail the first test.
  `actionable_tasks` filters and sorts by `task.id`. Rejected: a `Task`
  method — the schema stays policy-free, and the wake imports `room`.
- **Cursor is the pair of newest comment ids, not the API `since` stamp.**
  The room read unions issue comments and review comments (the gate's
  finding tasks), and those ids are separate sequences, so the cursor is
  `<issue>:<review>`. Each poll re-reads the whole room (a reply's state
  depends on its opener) and surfaces a task only when its last comment id
  exceeds the component for that comment's endpoint; each component then
  advances to the highest id seen on its endpoint. `--since` defaults to
  `0:0` (a bare integer is the issue component), so
  a fresh watch surfaces the backlog. Rejected: `comments?since=<ISO>` — it
  filters on `updated_at`, which a `join` re-upsert bumps, and drops openers.
- **Union order is `created_at` then id.** Issue comments and review
  comments are numbered in separate sequences, so ordering the union by id
  can place an issue-comment reply before the review-comment opener it
  answers and `build_tasks` would drop it as an orphan. The `room-gh-seam`
  requirement is modified to order by `(created_at, id)`; the watch cursor
  pair is unaffected because it tracks each endpoint's highest id
  separately. Rejected: keeping id order and special-casing replies — the
  schema's task builder is order-driven by design.
- **One fetch per poll.** `_read_comments(gh, repo, number)` is the paginated
  fetch extracted from `_read_room`; `_room_from_comments(comments)` builds
  `(cards, tasks)` with the same warn-and-skip; `_read_room` composes them.
  `watch` calls them separately so the raw list also serves
  `_last_comment(comments, task)`: the last comment whose id is `task.id` or
  whose marker's `taskId` is `task.id`.
- **No card is required to watch.** A watcher without a card gets an empty
  `skills` tuple, so only `to == agent` matches — a human login may watch
  tasks addressed to it, as room-cli-verb allows a human addressee.
- **Cap is enforced in the loop (Q1).** For each actionable task where
  `at_round_cap(task, agent, max_rounds)`: with a card, post a Message at
  `failed`, reason `round-cap`, round `next_round(task, agent)`, text `round
  cap (<max_rounds>) reached`, and print `task <id>: round cap reached —
  posted failed (round-cap)` on stderr; without one, print `WARNING: task
  <id>: round cap reached; join the room to close it`. Either way the task is
  not surfaced and the poll continues. `max_rounds` is `--max-rounds` or
  `resolve_room(root)[1]`.
- **NDJSON line.** One `json.dumps(obj, sort_keys=True)` line per surfaced
  task: the task object as `list --json` renders it plus `context`, `comment`
  (last comment id), `text`, `url` (its `html_url`), and `cursor`. After a
  poll that printed at least one line the verb exits `0`.
- **Loop and seams.** `main(argv=None, gh=None, sleep=time.sleep,
  clock=time.monotonic)`; `--interval` (float, default `30`, usage error when
  not `> 0`), `--timeout` (float, no default — Q2), `--once`. After an empty
  poll: `--once` ends the watch; else if `--timeout` is set and `clock() -
  start >= timeout` it ends; else `sleep(interval)` and repeat. An empty end
  prints `watch: no actionable task on <context> (cursor <n>)` on stderr and
  exits `0` with empty stdout (Q3). `KeyboardInterrupt` exits `130` with no
  traceback; a `RoomError` exits `1` as in every verb — no poll swallows it.
- **Banner.** The `room` line in `plugins/s/bin/shipd` reads `join, list,
  message, close, watch`; `cli-dispatch` lists no sub-verbs, so no `shipd-cli`
  delta is needed.

Risk: a tight poll hammers the API; guarded by the `> 0` check and the 30 s
default. Risk: `room.py` helper names drift before merge; the first task
re-reads the merged module and stops on any missing symbol.

## Questions and answers

### Q1: Who posts the round-cap failure that watch detects?
- **Question:** Options: (1) `watch` posts `failed`/`round-cap` itself when
  the watcher has a card, never surfaces the task, and keeps polling; (2)
  `watch` surfaces the task with `at_cap: true` and leaves the post to the
  agent's next `message`. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1 — the epic's loop diagram puts the cap branch inside
  the watch loop ahead of the NDJSON node, posting `failed`/`round-cap` and
  returning to the poll, and the member table assigns round-cap enforcement
  to `room-watch`. The card-only sub-clause is the planner's, from the
  epic's identity rule (`agent` must match a card).
- **Cited:** epic/pr-room

### Q2: What does `--timeout` default to?
- **Question:** Options: (1) no default — poll until a task arrives or the
  process is interrupted; (2) a bounded default of 600 seconds.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the epic names the three exits as `--once`, a task,
  and `--timeout`, so the bound is the caller's; `/s:room` passes one when
  it runs unattended.
- **Queued:** q-pr-room-watch-timeout-default
- **Relied on by:** room-skill

### Q3: What exit code ends an empty watch?
- **Question:** Options: (1) exit `0` with empty stdout and one stderr line,
  as `claim --wait --timeout` does when it times out empty; (2) a distinct
  nonzero code so a loop can branch without reading stdout.
  Recommendation: (1). (The queued block lists the nonzero option first.)
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the library's only empty-wait precedent
  (`build-task-coordination`, "Wait times out empty") exits zero with a
  stderr note, and `3` and `4` already mean guard refusal and delta-check
  findings in `spec-status`; a caller branches on empty stdout.
- **Queued:** q-pr-room-watch-empty-exit-code
- **Relied on by:** room-skill, room-action-wake

## Readiness attestation

### Problem and motivation

After the verbs land, no agent can learn when it is its turn, so the skill
and the CI wake cannot wait on a task.

Evidence:

- Epic `pr-room` Decision "Local poll first, CI wake second": `watch` "is the
  first wake path"; Design seams: "the CI wake depends on the watch's
  'actionable' predicate".
- `room-cli-verb` plan `### Non-goals`: "No `watch`, no `since` cursor, no
  actionable-task predicate (`room-watch`)".

### Scope and non-goals

The change adds the verb, the predicate, the loop, its tests, and the banner
word; skill, workflow, gate, schema, and config stay with their owners.

Evidence:

- Epic `pr-room` Changes table rows `room-skill`, `room-action-wake`,
  `room-gate-adoption`.
- `room-cli-verb` plan: `resolve_room` ignores unknown members "so
  `room-watch` can add its own later" — none is needed.

### Affected capabilities and files

One capability and four files, because the verb and loop live in the
existing script, the tests in the existing suite, the banner in the binary,
and the version in the manifest.

Evidence:

- Capability `pr-room` (added by `room-schema`; this delta is `ADDED` only).
- Files: `plugins/s/skills/room/scripts/room.py` and
  `plugins/s/skills/room/tests/test_room.py` (both unmerged, from
  `room-cli-verb`), `plugins/s/bin/shipd:167-170` (banner block),
  `plugins/s/.claude-plugin/plugin.json:4` (`0.6.283` on `main`).
- Precedent: `plugins/s/skills/review/scripts/review_gate.py:139-143`
  (runner), `:681` (comment read).
- Runnable premise: `python3 plugins/s/skills/build/scripts/version_guard.py
  --base main --head HEAD` → exit 0 on the untouched worktree.
- Runnable premise: `gh api --help` on gh 2.95.0 → lists `--paginate` and
  `--slurp`.
- Runnable premise: `spec_status.py wiki-show --personal` → no personal
  store; the memory consultation was skipped.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Cursor as comment id, one fetch per poll, module-level predicate, no card
  required, injected `sleep`/`clock`: settled by investigation of the epic,
  `review_gate.py`, and the two sibling plans.
- Cap posting in the loop: settled by the oracle, Q1; card-only posting by
  investigation of the epic's identity decision.
- No default timeout: PLANNER default, Q2.
- Empty-watch exit `0`: PLANNER default, Q3.
