## ADDED Requirements

### Requirement: Actionable-task predicate
id: room-actionable-predicate

`room.py` SHALL expose a module-level, I/O-free function
`is_actionable(task, agent, skills=())` over a `room_schema.Task` that
returns true exactly when `task.state` is `input-required`, `task.last_agent`
is not `agent`, and either `task.to` equals `agent` or `task.to` is `None`
and `task.skill` is a member of `skills`; and
`actionable_tasks(tasks, agent, skills=())` returning the matching tasks
ordered by `id`. A task in `submitted`, `working`, `completed`, `failed`, or
`canceled` SHALL never be actionable.

#### Scenario: Addressed task is actionable for its addressee only
- **WHEN** a task is `input-required` from `codex-a` to `claude-b`
- **THEN** `is_actionable(task, "claude-b")` is true and
  `is_actionable(task, "codex-a")` and `is_actionable(task, "other")` are
  false

#### Scenario: Unaddressed task matches by skill
- **WHEN** a task is `input-required` with no `to` and skill `review-finding`
- **THEN** `is_actionable(task, "claude-b", ("review-finding",))` is true and
  `is_actionable(task, "claude-b", ())` is false

#### Scenario: Own last message is never actionable
- **WHEN** a task is `input-required` to `claude-b` whose last message was
  posted by `claude-b`
- **THEN** `is_actionable(task, "claude-b")` is false

#### Scenario: Terminal and working tasks are skipped
- **WHEN** tasks to `claude-b` sit at `completed`, `failed`, `canceled`,
  `working`, and `submitted`
- **THEN** `actionable_tasks(tasks, "claude-b")` is empty

### Requirement: Watch polls and emits newly actionable tasks
id: room-watch-verb

`room.py watch <pr> [--since CURSOR] [--interval S] [--timeout S] [--once]
[--max-rounds N]` SHALL resolve the agent as every room verb does, SHALL
not require a card, and on each poll SHALL read the room once through the
`gh` runner, take `skills` from the card named `agent` (empty when none),
and surface every task from `actionable_tasks` whose last comment id is
greater than the cursor component for that comment's endpoint. The cursor
(`--since`, default `0:0`) SHALL be the pair `<issue>:<review>` — the highest
issue-comment id and the highest review-comment id read — because the room
read unions `issues/<n>/comments` and `pulls/<n>/comments`, whose ids are
separate sequences; a bare integer SHALL be accepted as the issue component
with the review component `0`. For each surfaced task it SHALL print one
line, `json.dumps(obj, sort_keys=True)`, holding the task fields
`list --json` prints plus `context`, `comment` (the last comment id),
`text` (the last message text), `url` (that comment's `html_url`), and
`cursor` (the pair as a string); after a poll that printed at least one line
the verb SHALL exit `0`. Each cursor component SHALL advance to the highest
id read from its endpoint after every poll. `--interval` (seconds, default `30`) SHALL
be rejected as a usage error when not greater than `0`.

#### Scenario: First poll surfaces the backlog and exits
- **WHEN** `watch 7` runs as `claude-b` on a PR holding a task to `claude-b`
  at `input-required` and a task to `codex-a`
- **THEN** stdout holds exactly one line whose `task` is the first task's id,
  `cursor` is the `<issue>:<review>` pair of the highest ids read, and the
  exit code is `0` after a single room read

#### Scenario: Cursor hides what was already seen
- **WHEN** `watch 7 --since <cursor> --once` runs with the cursor component
  for the actionable task's endpoint equal to its last comment id
- **THEN** stdout is empty

#### Scenario: Skill match without a card is empty
- **WHEN** `watch 7 --once` runs as `claude-b` with no card for `claude-b` and
  an unaddressed task with skill `review-finding`
- **THEN** stdout is empty and no `Error:` line is printed

#### Scenario: A task becomes actionable on a later poll
- **WHEN** `watch 7` runs with an injected `sleep` whose second call appends a
  task to `claude-b` to the fake PR
- **THEN** the first two polls print nothing, the third prints that task,
  `sleep` was called twice with `30`, and the exit code is `0`

### Requirement: Watch enforces the round cap
id: room-watch-round-cap

If an actionable task satisfies `room_schema.at_round_cap(task, agent,
max_rounds)`, then `watch` SHALL not surface it; when a card named `agent`
exists, it SHALL post on that task a Message at state `failed` with
`metadata.reason` `round-cap`, `metadata.round` `next_round(task, agent)`,
and text `round cap (<max_rounds>) reached`, and print `task <id>: round cap
reached — posted failed (round-cap)` on stderr; when no card exists, it SHALL
print `WARNING: task <id>: round cap reached; join the room to close it` and
post nothing. In both cases the poll continues as if the task were absent.

#### Scenario: Cap posts failed and keeps polling
- **WHEN** `watch 7 --once --max-rounds 6` runs as `claude-b` with a card and
  a task to `claude-b` at round 6 whose last agent is `codex-a`
- **THEN** one POST carries `metadata` `{"reason":"round-cap","round":7,
  "state":"failed"}`, stdout is empty, and the exit code is `0`

#### Scenario: Cap without a card is a warning
- **WHEN** the same watch runs as `claude-b` with no card
- **THEN** nothing is posted, stderr holds the `WARNING: task <id>: round cap
  reached` line, and stdout is empty

### Requirement: Watch exit semantics
id: room-watch-exit

After a poll that surfaced no task, `watch` SHALL end when `--once` is set
or when `--timeout` is set and the injectable monotonic clock reports at
least that many seconds since the watch started; otherwise it SHALL call the
injectable `sleep` with `--interval` and poll again. A watch that ends
without surfacing a task SHALL print `watch: no actionable task on <context>
(cursor <n>)` on stderr, print nothing on stdout, and exit `0`, so a caller
branches on empty stdout. A `KeyboardInterrupt` SHALL exit `130`
with no traceback; a failed `gh` call SHALL be reported as a single `Error:
<reason>` line with exit `1`, exactly as the other verbs report it.
`main(argv=None, gh=None, sleep=time.sleep, clock=time.monotonic)` SHALL
accept the two seams as keyword arguments.

#### Scenario: Once with nothing exits zero and empty
- **WHEN** `watch 7 --once` runs on a PR with no actionable task
- **THEN** stdout is empty, stderr ends with the `watch: no actionable task`
  line naming the cursor, and the exit code is `0`

#### Scenario: Timeout ends the watch
- **WHEN** `watch 7 --timeout 60 --interval 20` runs with an injected clock
  advancing 25 seconds per call and no task ever appears
- **THEN** `sleep` is called until the clock passes 60, the verb exits `0`
  with empty stdout,
  and the comments read was recorded once per poll

#### Scenario: Failed read is fatal
- **WHEN** the runner answers the comments read with a non-zero code
- **THEN** the verb prints one `Error: ` line and exits `1` without sleeping

### Requirement: Watch tests, banner, and version
id: room-watch-tests

The watch verb, the predicate, and the cap path SHALL be covered in
`plugins/s/skills/room/tests/test_room.py` through `main(argv, gh=FakeGh(...),
sleep=..., clock=...)` with no real sleep and no network, discovered by the
`ci` workflow's `Run room test suite` step; the `shipd` usage banner SHALL
name `watch` on its `room` line; and the change SHALL advance the plugin
version in `plugins/s/.claude-plugin/plugin.json` by one patch above the
value `main` carries.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests -v`
  runs with no network
- **THEN** it reports `OK` and the watch tests completed without a real sleep

#### Scenario: Banner names watch
- **WHEN** `shipd --help` runs
- **THEN** the `room` line reads `join, list, message, close, watch`

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`

## MODIFIED Requirements

### Requirement: Room verbs reach GitHub only through the gh seam
id: room-gh-seam
base: 5fc644b2cd31

`plugins/s/skills/room/scripts/room.py` SHALL expose `main(argv=None,
gh=None)` whose `gh` is a runner `gh(args, input=None) -> (rc, stdout,
stderr)` defaulting to a `subprocess` call of the `gh` CLI, and every GitHub
read or write SHALL go through that runner. The module SHALL import only
the standard library, `room_schema` (its sibling), and the engine's
`spec_common` and `cli_common` from `skills/build/scripts/`. A room SHALL be
resolved as `gh pr view <pr> --json number,url` plus `gh repo view --json
nameWithOwner`, giving the context id `<owner>/<repo>#<number>`; the room's
comments SHALL be read as the union of `gh api
repos/<repo>/issues/<n>/comments?per_page=100 --paginate --slurp` and `gh api
repos/<repo>/pulls/<n>/comments?per_page=100 --paginate --slurp` — issue
comments carry room traffic, review comments carry the semantic-review
gate's finding tasks — the returned pages flattened and the union ordered
by `created_at` and then by comment id, because GitHub numbers issue
comments and review comments in separate sequences, so a reply posted as
an issue comment onto a review-comment opener must still follow its
opener; each comment is parsed with
`room_schema.parse_comments(body, author=<user.login>)` so a comment carrying
both a card and a Message contributes both. If a comment's
marker raises `SchemaError`, then the verb SHALL print one
`WARNING: comment <id>: <reason>` line on stderr and skip it. A failed `gh`
call SHALL be reported as a single `Error: <reason>` line and exit `1`;
invalid arguments SHALL exit `2` with usage text, per `cli-conventions`.

#### Scenario: Comments are paged and flattened
- **WHEN** the fake runner answers the comments call with two slurped pages
- **THEN** `list` reports the cards and tasks of both pages, and the recorded
  call carries `--paginate` and `--slurp`

#### Scenario: A reply follows its opener across endpoints
- **WHEN** a review comment with id `900` created at `10:00` opens a task
  and an issue comment with id `50` created at `10:05` replies to it
- **THEN** the room read orders the opener before the reply and the task
  holds both messages, the reply last

#### Scenario: A failed gh call is one Error line
- **WHEN** the runner returns a non-zero code for `gh pr view`
- **THEN** stderr carries a single `Error: ` line and the exit code is `1`

#### Scenario: A malformed marker is skipped with a warning
- **WHEN** one comment holds `<!-- shipd-room {not json} -->`
- **THEN** `list` prints `WARNING: comment <id>:` on stderr, exits `0`, and
  reports every other comment
