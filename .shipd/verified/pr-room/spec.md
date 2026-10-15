# pr-room

### Requirement: Room comment marker format
id: room-marker-format

`room_schema.render_comment` SHALL emit, as line 1, `<!-- shipd-room <json> -->`
for a Message and `<!-- shipd-room-card <json> -->` for an Agent Card, where
`<json>` is the object serialized with `separators=(",", ":")`,
`sort_keys=True`, and every `>` replaced by `\u003e`; a blank line and the
human prose SHALL follow. `room_schema.parse_comment(body, author=None)` SHALL
find the first such marker anywhere in the body and return the parsed
`AgentCard` or `Message`; if the body carries no marker, then it SHALL return a
`Message` with `role` `user`, one text part holding the body, `agent` set to
`author`, and no `task_id`. `room_schema.parse_comments(body, author=None)`
SHALL return every marker's parsed object in body order as a list, so a
comment carrying a card marker and a Message marker — the semantic-review
gate's summary — yields both; a body with no marker SHALL yield a one-element
list holding the same `user` Message `parse_comment` returns. If the marker JSON does not parse or fails
validation, then `parse_comment` SHALL raise `SchemaError`. The module SHALL
import nothing beyond the standard library and SHALL import neither
`subprocess` nor any network module.

#### Scenario: Round-trip through render and parse
- **WHEN** a Message whose text part contains `-->` is rendered and the result
  is parsed
- **THEN** the rendered first line is a single `<!-- shipd-room … -->` HTML
  comment, and the parsed Message equals the original

#### Scenario: Marker below a severity line still parses
- **WHEN** a body opens with `**● high — x**` and carries the marker on its
  last line
- **THEN** `parse_comment` returns the Message held by that marker

#### Scenario: Unmarked comment is a human message
- **WHEN** `parse_comment("looks good", author="octocat")` runs
- **THEN** it returns a Message with role `user`, agent `octocat`, text
  `looks good`, and `task_id` `None`

#### Scenario: Malformed marker raises
- **WHEN** the body holds `<!-- shipd-room {not json} -->`
- **THEN** `parse_comment` raises `SchemaError`

### Requirement: Agent Card shape
id: room-agent-card

An `AgentCard` SHALL carry `name` (required, non-empty), `description`,
`skills` (a tuple of skill-id strings), `version`, `harness`, and `extra`
holding every unknown marker key. The card prose SHALL open with
`**<name>** joined the room`, followed by ` from <harness>` when `harness` is
set and ` — skills: <a, b>` when `skills` is non-empty, then the description
on its own paragraph when set.

#### Scenario: Card renders its prose
- **WHEN** a card named `codex-reviewer` with harness `codex` and skills
  `review-finding` is rendered
- **THEN** line 1 is a `shipd-room-card` marker and the prose reads
  `**codex-reviewer** joined the room from codex — skills: review-finding`

#### Scenario: Nameless card is rejected
- **WHEN** a `shipd-room-card` marker has no `name`
- **THEN** `parse_comment` raises `SchemaError`

#### Scenario: Unknown card keys survive a round-trip
- **WHEN** a card marker carries a key `securitySchemes`
- **THEN** the parsed card holds it in `extra` and re-rendering emits it again

### Requirement: Message shape
id: room-message-shape

A `Message` SHALL carry `role` (`user` or `agent`), `parts` (a tuple of part
dicts; a part with `kind` `text` carries `text`), `context_id`, `agent`,
`task_id` (an int, or `None` for a task opener), `metadata`, and `extra`. The
wire keys SHALL be the A2A names `role`, `parts`, `contextId`, `taskId`,
`agent`, `metadata`. The properties `state`, `to`, `round`, `reason`, and
`skill` SHALL read the matching `metadata` keys, and `text` SHALL join the text
parts with blank lines and be the rendered prose. An agent message SHALL be
rejected with `SchemaError` when `agent` or `context_id` is empty, when
`metadata.state` is not one of `submitted`, `working`, `input-required`,
`completed`, `failed`, `canceled`, or when `metadata.round` is present and not
an int of at least 1.

#### Scenario: State lives in metadata
- **WHEN** an agent Message with state `input-required`, to `codex-reviewer`,
  round 1 is rendered
- **THEN** the marker JSON holds `"metadata":{"round":1,"state":"input-required","to":"codex-reviewer"}`
  and no top-level `state` key

#### Scenario: Unknown state is rejected
- **WHEN** a marker carries `metadata.state` `open`
- **THEN** `parse_comment` raises `SchemaError`

#### Scenario: Non-text parts are kept but not rendered
- **WHEN** a Message holds a `text` part and a part of kind `data`
- **THEN** the prose shows only the text, and the parsed Message still holds
  both parts

### Requirement: Task view from a comment chain
id: room-task-view

`room_schema.build_tasks(entries)` SHALL take `(comment_id, Message)` pairs in
comment order and return a list of `Task` views ordered by id. An agent Message
whose `task_id` is `None` SHALL open a task whose `id` is its comment id; a
Message whose `task_id` names an opened task SHALL be appended to it; a Message
naming an unknown task, and every `user` Message, SHALL be skipped. A `Task`
SHALL carry `id`, `context_id`, `opener` (the opening agent), `skill` (the
opener's `metadata.skill`), `messages`, and — from its last message — `state`,
`to`, `round`, `reason`, and `last_agent`.

#### Scenario: Reply updates the task view
- **WHEN** comment 10 opens a task from `a` to `b` at `input-required`, and
  comment 12 with `taskId` 10 from `b` posts `completed` at round 2
- **THEN** `build_tasks` returns one Task with id 10, opener `a`, state
  `completed`, last_agent `b`, round 2

#### Scenario: Orphan reply is skipped
- **WHEN** the only entry is a Message with `taskId` 99 and no comment 99 was
  seen
- **THEN** `build_tasks` returns an empty list

### Requirement: Task state machine and round cap
id: room-state-machine

`room_schema.next_state(current, requested)` SHALL be the only transition
table: when `current` is `None`, it SHALL accept `submitted` and
`input-required`; when `current` is `submitted`, `working`, or
`input-required`, it SHALL accept every state except `submitted`; when
`current` is `completed`, `failed`, or `canceled`, it SHALL raise
`InvalidTransition` for every request. It SHALL return the accepted state.
`next_round(task, agent)` SHALL return `task.round` when `agent` equals
`task.last_agent` and `task.round + 1` otherwise, and
`at_round_cap(task, agent, max_rounds)` SHALL be true exactly when
`next_round(task, agent)` exceeds `max_rounds`.

#### Scenario: Opener may start addressed
- **WHEN** `next_state(None, "input-required")` runs
- **THEN** it returns `input-required`

#### Scenario: Terminal states absorb
- **WHEN** `next_state("completed", "working")` runs
- **THEN** it raises `InvalidTransition`

#### Scenario: Same agent keeps the round
- **WHEN** a task at round 3 with last_agent `b` is asked `next_round` for `b`
  and then for `a`
- **THEN** it returns 3 and then 4

#### Scenario: Cap is checked before posting
- **WHEN** a task at round 6 with last_agent `b` is asked
  `at_round_cap(task, "a", 6)`
- **THEN** it returns true, and `at_round_cap(task, "b", 6)` returns false

### Requirement: Schema test coverage in ci
id: room-schema-tests

`room_schema.py` SHALL be covered by a unittest suite under
`plugins/s/skills/room/tests/` that performs no network access and covers the
marker round-trip, the human-message fallback, card and message validation,
the task view, the transition table, and the round cap; the `ci` workflow
SHALL discover it through a dedicated `Run room test suite` step, and the
change SHALL advance the plugin version in `plugins/s/.claude-plugin/plugin.json`.

#### Scenario: ci discovers the room suite
- **WHEN** the ci workflow's room test step runs
- **THEN** `python3 -m unittest discover -s plugins/s/skills/room/tests -v`
  passes with no network access

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits 0 because the manifest version advanced

### Requirement: Room verbs reach GitHub only through the gh seam
id: room-gh-seam

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

### Requirement: Agent identity resolution
id: room-agent-identity

Every room verb SHALL resolve the acting agent's name from `--agent`, then
the `SHIPD_ROOM_AGENT` environment variable, then the `agent` member of
`spec_common.resolve_room(root)` where `root` is `--root` (default: the
working directory); if none supplies a name, then the verb SHALL fail with
usage text and exit `2`. `message` and `close` SHALL refuse with `Error:
agent '<name>' has not joined <context> — run shipd room join` and exit `1`
when no `shipd-room-card` comment on the PR carries that name; `join` and
`list` SHALL not require a card. `max_rounds` SHALL come from the same
resolver, overridable by `--max-rounds`.

#### Scenario: Environment supplies the name
- **WHEN** `message` runs without `--agent` and with `SHIPD_ROOM_AGENT=codex-a`
  in the environment
- **THEN** the posted Message carries `agent` `codex-a`

#### Scenario: No name is a usage error
- **WHEN** `join` runs with no `--agent`, no `SHIPD_ROOM_AGENT`, and no
  `room.agent` in any config layer
- **THEN** the verb exits `2` with usage text naming the three sources

#### Scenario: Unjoined agent cannot post
- **WHEN** `message` runs as `codex-a` on a PR whose only card is `claude-b`
- **THEN** no comment is posted and the verb exits `1` with the
  `has not joined` Error line

### Requirement: Join upserts the agent card
id: room-join-verb

`room.py join <pr> [--agent NAME] [--skill S ...] [--description TEXT]
[--harness H]` SHALL render an `AgentCard` (`name`, `skills`, `description`,
`harness`, and `version` read from the plugin manifest adjacent to the
skill tree) with `room_schema.render_comment` and SHALL edit in place
(`PATCH repos/<repo>/issues/comments/<id>`) the existing card comment whose
`name` equals the agent, or create one (`POST
repos/<repo>/issues/<n>/comments`) when none exists. It SHALL print one JSON
object `{"comment": <id>, "agent": <name>, "url": <html_url>}` on stdout and
`joined <context> as <name>` on stderr, and exit `0`.

#### Scenario: First join creates the card
- **WHEN** `join 7 --agent codex-a --skill review-finding --harness codex`
  runs on a PR with no cards
- **THEN** one POST is recorded whose body's first line is a
  `shipd-room-card` marker naming `codex-a` with skill `review-finding`

#### Scenario: Second join edits the same comment
- **WHEN** `join` runs again as `codex-a` with a new description
- **THEN** a PATCH on the existing comment id is recorded and no second card
  comment exists

### Requirement: List reports cards and tasks
id: room-list-verb

`room.py list <pr> [--json]` SHALL read the room once and print, in text
mode, a `room <context>` header, a `cards:` block with one line per card
(`name`, `harness`, `skills`, `version`) and a `tasks:` block with one line
per `Task` from `room_schema.build_tasks` (`#<id>`, `state`, `from <opener>`,
`to <addressee|->`, `round <n>`, `last <last_agent>`, and `skill <s>` when
set); with `--json` it SHALL print one object `{"context", "cards": [card
dicts], "tasks": [{"id", "state", "opener", "to", "round", "reason",
"last_agent", "skill", "messages": <count>}]}`. A room with no cards or no
tasks SHALL print `(none)` under that block.

#### Scenario: Two cards and one open task
- **WHEN** the PR holds cards for `codex-a` and `claude-b` and a task opened
  by `codex-a` to `claude-b` at `input-required`
- **THEN** text output lists both cards and `#<id>  input-required  from
  codex-a  to claude-b  round 1  last codex-a`, and `--json` carries the
  same two cards and one task with `messages` `1`

#### Scenario: Human comments are not tasks
- **WHEN** the PR holds only unmarked comments
- **THEN** both blocks print `(none)` and the exit code is `0`

### Requirement: Message opens or advances a task
id: room-message-verb

`room.py message <pr> (--new | --task ID) [--to AGENT] [--state S]
[--skill S] [--max-rounds N] <text>` SHALL post a `Message` (`role` `agent`,
one text part, the room's context id) as an issue comment. With `--new`
the Message SHALL carry no `taskId`, `metadata.round` `1`, `metadata.skill`
from `--skill` when given, and `metadata.state` `next_state(None, S)` where
`S` defaults to `input-required` when `--to` is given and `submitted`
otherwise. With `--task ID` the id SHALL name a task in the room's
`build_tasks` view (else `Error: task <id> not found on <context>`, exit
`1`); the Message SHALL carry `taskId` `ID`, `metadata.round`
`next_round(task, agent)`, and `metadata.state` `next_state(task.state, S)`
where `S` defaults to `input-required` when `--to` is given and `working`
otherwise; an `InvalidTransition` SHALL be reported as `Error: task <id> is
<state>; no transition to <S>` with exit `1` and nothing posted. Before
posting a `--task` reply, if `at_round_cap(task, agent, max_rounds)` holds,
then the verb SHALL post instead a Message at state `failed` with
`metadata.reason` `round-cap` and text `round cap (<max_rounds>) reached`,
and SHALL exit `1` with `Error: round cap reached on task <id> — posted
failed (round-cap)`. `metadata.to` SHALL be set from `--to` when given. On
success the verb SHALL print `{"comment": <id>, "task": <task id>, "state":
<state>, "round": <n>, "url": <html_url>}` on stdout and exit `0`.

#### Scenario: Addressed opener starts at input-required
- **WHEN** `message 7 --new --to claude-b "please check"` runs as `codex-a`
- **THEN** the posted marker holds no `taskId`, `metadata`
  `{"round":1,"state":"input-required","to":"claude-b"}`, and stdout's
  `task` equals the new comment id

#### Scenario: Reply advances the round for the other party
- **WHEN** task 10 is at `input-required`, round 1, last agent `codex-a`, and
  `message 7 --task 10 --to codex-a --state completed "done"` runs as
  `claude-b`
- **THEN** the posted marker holds `taskId` 10 and `metadata`
  `{"round":2,"state":"completed","to":"codex-a"}`

#### Scenario: Terminal task refuses a reply
- **WHEN** task 10 is `completed` and `message 7 --task 10 "more"` runs
- **THEN** nothing is posted and the verb exits `1` with the `no transition`
  Error line

#### Scenario: Cap posts failed and exits one
- **WHEN** task 10 is at round 6 with last agent `codex-a`, `--max-rounds 6`,
  and `message 7 --task 10 "again"` runs as `claude-b`
- **THEN** the only post carries `metadata` `{"reason":"round-cap","round":7,
  "state":"failed"}`, and the verb exits `1` with the `round cap reached`
  Error line

### Requirement: Close posts the terminal message
id: room-close-verb

`room.py close <pr> --task ID [--state completed|canceled|failed]
[--reason TEXT] [text]` SHALL post a Message on task `ID` at
`next_state(task.state, S)` with `S` defaulting to `completed`,
`metadata.round` `next_round(task, agent)`, `metadata.reason` from
`--reason` when given, and the text defaulting to `closed: <S>` (plus ` —
<reason>` when set). It SHALL apply no round cap, SHALL report an
`InvalidTransition` exactly as `message` does, and SHALL print the same JSON
object `message` prints on success.

#### Scenario: Default close completes
- **WHEN** `close 7 --task 10` runs as `claude-b` on an `input-required` task
- **THEN** the posted marker holds `metadata.state` `completed` and no
  `reason`

#### Scenario: Close with a reason at the cap still posts
- **WHEN** task 10 is at round 6 with last agent `codex-a`, max rounds 6, and
  `close 7 --task 10 --state failed --reason stalled` runs as `claude-b`
- **THEN** the post carries `metadata` `{"reason":"stalled","round":7,
  "state":"failed"}` and the verb exits `0`

### Requirement: Room verb tests and version
id: room-verb-tests

`room.py` SHALL be covered by `plugins/s/skills/room/tests/test_room.py`, a
unittest suite driving `main(argv, gh=FakeGh(...))` through a stateful fake
runner that answers `pr view`, `repo view`, the comments read, and the
comment POST/PATCH calls, recording each invocation; the suite SHALL spawn
no `gh` process and reach no network, and SHALL be discovered by the `ci`
workflow's existing `Run room test suite` step. The change SHALL advance the
plugin version in `plugins/s/.claude-plugin/plugin.json` by one patch above
the value `main` carries.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests -v`
  runs with no network
- **THEN** it reports `OK`, covering both test files

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`

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

### Requirement: Room wake workflow template
id: room-wake-workflow-template

The plugin SHALL ship `plugins/s/integrations/copilot/room-wake.yml`, whose
first line is `# shipd-copilot v{version}`, triggered on `issue_comment` and
`pull_request_review_comment` with `types: [created]`, and composed of three
jobs. The `guard` job SHALL run only when `vars.SHIPD_ROOM_AGENT` is
non-empty, the comment body contains `<!-- shipd-room `, and the event is a
review comment or an issue comment on a pull request; it SHALL bind
`github.token` and never `COPILOT_GITHUB_TOKEN`, check out the default
branch, and report not-actionable when the `COPILOT_GITHUB_TOKEN` secret is
absent. Otherwise it SHALL run the bundled
`.github/shipd-room/skills/room/scripts/room.py watch <pr> --once --since
<cursor>` as the agent `SHIPD_ROOM_AGENT` names — the cursor being the
`<issue>:<review>` pair `watch` accepts, `<id - 1>:0` for an `issue_comment`
trigger and `0:<id - 1>` for a `pull_request_review_comment` trigger — treat
empty stdout
as not actionable, and act only on the NDJSON line whose `comment` equals
the triggering comment id and whose `to` equals that agent; when acting it
SHALL `join` with `--harness copilot-cli` if no card of that name exists,
post `working` on the task, and output `actionable`, `pr`, `task`, `asker`
(the line's `last_agent`) and `text`. The `run` job SHALL depend on an
actionable guard, bind only `COPILOT_GITHUB_TOKEN`, check out
`refs/pull/<pr>/head` with `persist-credentials: false`, install
`@github/copilot@1.0.80`, run `copilot -p` with `--allow-all-tools` under a
`timeout` defaulting to 600 seconds, and output the reply truncated to
60000 characters. The `reply` job SHALL run with `if: always()` whenever the
guard was actionable, bind `github.token` and never `COPILOT_GITHUB_TOKEN`,
check out the default branch, read the reply only through `env:`, and post
via the bundled `room.py message <pr> --task <task> --to <asker>`: state
`input-required` with the marker stripped when the reply's last non-blank
line is exactly `<!-- shipd-room-reply: input-required -->`, else
`completed`. If the `run` job did not succeed or the reply is empty, then
the `reply` job SHALL instead post `close --task <task> --state failed
--reason wake-runner-failed`. Every `room.py` invocation SHALL run through
`/usr/bin/env -i` with an explicit `PATH=/usr/bin:/bin` and
`/usr/bin/python3 -B`.

#### Scenario: Addressed task is picked up
- **WHEN** the guard script runs with a stub `room.py` whose `watch` prints
  a line with `comment` equal to the event id and `to` equal to
  `SHIPD_ROOM_AGENT`
- **THEN** the guard outputs `actionable=true` with that task, asker and
  text, and the stub recorded a `message --task <id> --state working` call

#### Scenario: Other or empty lines are ignored
- **WHEN** the stub `watch` prints nothing, or a line for another comment
  id, or a line whose `to` names another agent
- **THEN** the guard outputs `actionable=false`, exits `0`, and the stub
  recorded no `message` or `join` call

#### Scenario: Reply marker selects input-required
- **WHEN** the reply script runs on a reply ending with the line
  `<!-- shipd-room-reply: input-required -->`
- **THEN** the stub recorded `message --task <id> --to <asker> --state
  input-required` with text that no longer holds the marker line

#### Scenario: Plain reply completes, failed run closes
- **WHEN** the reply script runs on a plain reply, and again with the run
  result `failure`
- **THEN** the first records `--state completed`; the second records `close
  --task <id> --state failed --reason wake-runner-failed`

#### Scenario: Credentials never share a job
- **WHEN** the template text is split into its three jobs
- **THEN** `COPILOT_GITHUB_TOKEN` is bound only in `run`, `github.token`
  only in `guard` and `reply`, and `run` checks out with
  `persist-credentials: false`

### Requirement: Room wake template tests
id: room-wake-tests

The template SHALL be covered by
`plugins/s/skills/room/tests/test_room_wake.py`, which extracts the guard
and reply `run:` scripts from the template, executes them with `bash`
in a temporary working directory holding a recording stub `room.py` at the
bundled path, with the `/usr/bin/python3` literal rewritten to the test
interpreter as the gate tests rewrite theirs, and asserts the triggers, the job split, the CLI pin and the
marker line; the suite SHALL need no network and be discovered by the `ci`
workflow's `Run room test suite` step.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests -v`
  runs with no network
- **THEN** it reports `OK`, including the `test_room_wake` cases
