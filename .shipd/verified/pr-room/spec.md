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
gate's finding tasks — the returned pages flattened and the union ordered by
comment id, each comment parsed with
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
