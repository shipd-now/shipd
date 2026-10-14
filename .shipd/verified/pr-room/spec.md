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
