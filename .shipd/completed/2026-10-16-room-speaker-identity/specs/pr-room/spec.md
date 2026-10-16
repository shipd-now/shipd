## MODIFIED Requirements

### Requirement: Agent Card shape
id: room-agent-card
base: bf3ca2d13969

An `AgentCard` SHALL carry `name` (required, non-empty), `description`,
`skills` (a tuple of skill-id strings), `version`, `harness`, `role` (an
optional string, `""` when absent), and `extra` holding every unknown marker
key. The marker SHALL carry a `role` key only when `role` is non-empty. The
card prose SHALL open with the speaker heading line `### ☕ shipd · <name>`,
followed by ` · <role>` when `role` is set and ` (for @<login>)` when a login
is supplied to the renderer. The next line SHALL be `<sub>joined the room</sub>`,
with ` from <harness>` when `harness` is set and ` · skills: <a, b>` when
`skills` is non-empty inside the `<sub>`, then the description on its own
paragraph when set.

#### Scenario: Card renders its prose
- **WHEN** a card named `codex-reviewer` with harness `codex`, role
  `reviewer`, and skills `review-finding` is rendered with login `mikkel`
- **THEN** line 1 is a `shipd-room-card` marker holding `"role":"reviewer"`
  and the prose reads `### ☕ shipd · codex-reviewer · reviewer (for @mikkel)`
  then `<sub>joined the room from codex · skills: review-finding</sub>`

#### Scenario: A card without role or login drops those segments
- **WHEN** a card named `x` with no role is rendered with no login
- **THEN** the heading reads `### ☕ shipd · x` and the marker has no `role` key

#### Scenario: Nameless card is rejected
- **WHEN** a `shipd-room-card` marker has no `name`
- **THEN** `parse_comment` raises `SchemaError`

#### Scenario: Unknown card keys survive a round-trip
- **WHEN** a card marker carries a key `securitySchemes`
- **THEN** the parsed card holds it in `extra` and re-rendering emits it again

#### Scenario: Role survives a round-trip
- **WHEN** a card marker carries `"role":"author"`
- **THEN** the parsed card's `role` is `author` and re-rendering emits it again

### Requirement: Message shape
id: room-message-shape
base: e6ee47d60d96

A `Message` SHALL carry `role` (`user` or `agent`), `parts` (a tuple of part
dicts; a part with `kind` `text` carries `text`), `context_id`, `agent`,
`task_id` (an int, or `None` for a task opener), `metadata`, and `extra`. The
wire keys SHALL be the A2A names `role`, `parts`, `contextId`, `taskId`,
`agent`, `metadata`. The properties `state`, `to`, `round`, `reason`, and
`skill` SHALL read the matching `metadata` keys, and `text` SHALL join the text
parts with blank lines. The rendered prose of an agent message SHALL open with
the speaker heading line `### ☕ shipd · <agent>`, followed by ` · <speaker
role>` when the renderer is given a role and ` (for @<login>)` when it is given
a login; the next line SHALL read `→ <to> · <state>`, dropping the `→ <to> · `
part when `metadata.to` is unset and the line itself when `metadata.state` and
`metadata.to` are both unset; then a blank line, then `text`. A `user`
message's prose SHALL be `text` alone. The speaker role and login are render
arguments, never stored in the marker. Parsing SHALL read the marker only, so
the heading never enters `text`. An agent message SHALL be rejected with
`SchemaError` when `agent` or `context_id` is empty, when `metadata.state` is
not one of `submitted`, `working`, `input-required`, `completed`, `failed`,
`canceled`, or when `metadata.round` is present and not an int of at least 1.

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
- **THEN** the prose shows only the text under the heading, and the parsed
  Message still holds both parts

#### Scenario: Agent prose names the speaker
- **WHEN** an agent Message from `copilot-ci` with state `completed`, to
  `builder`, and text `done` is rendered with role `ci` and login `mikkel`,
  and parsed back
- **THEN** the prose's first line is `### ☕ shipd · copilot-ci · ci (for @mikkel)`,
  the second is `→ builder · completed`, the text follows after a blank line,
  and the parsed Message's `text` is exactly `done`

#### Scenario: Prose without a recipient
- **WHEN** an agent Message with state `working` and no `to` is rendered with
  no role and no login
- **THEN** line 1 is `### ☕ shipd · <agent>` and line 2 is `working`

## ADDED Requirements

### Requirement: Join sets the card role
id: room-join-role

`room.py join` SHALL accept `--role {author,reviewer,ci}` and render the card
with that `role`; without `--role` the card carries no role, exactly as
`--skill` and `--description` are re-rendered from the flags given on each
join. Any other `--role` value SHALL exit `2` with usage text.

#### Scenario: Join with a role
- **WHEN** `join 7 --agent codex-a --role author` runs
- **THEN** the POSTed marker holds `"role":"author"` and the prose heading
  reads `### ☕ shipd · codex-a · author (for @bot)`

#### Scenario: Unknown role is a usage error
- **WHEN** `join 7 --agent codex-a --role boss` runs
- **THEN** nothing is posted and the verb exits `2`

### Requirement: Room verbs head their comments with the poster
id: room-poster-identity

Each of `join`, `message`, `close`, and `watch` SHALL, before its first post,
read the posting GitHub login once with `gh api user` and render every comment
it posts with that login in the speaker heading. `message`, `close`, and the
round-cap post SHALL take the heading's role from the posting agent's own card
(`role`), and no verb other than `join` SHALL accept a role flag. If the card
has no role, the heading SHALL drop the role segment. If the login read fails
or returns no login, the verb SHALL write a `warning:` line on stderr, drop the
`(for @<login>)` segment, and still post.

#### Scenario: Message heads with the card's role
- **WHEN** `message 7 --new "hi"` runs as `codex-a`, whose card has role
  `author`, and `gh api user` returns login `bot`
- **THEN** the POSTed body's prose opens `### ☕ shipd · codex-a · author (for @bot)`
  and `gh api user` was called once

#### Scenario: A failed login read still posts
- **WHEN** `gh api user` exits non-zero during `close`
- **THEN** stderr carries a `warning:` line, the terminal message is posted,
  and its heading has no `(for @` segment

#### Scenario: A card without a role drops the role segment
- **WHEN** `message` runs as an agent whose card has no `role`
- **THEN** the heading reads `### ☕ shipd · <agent> (for @<login>)`
