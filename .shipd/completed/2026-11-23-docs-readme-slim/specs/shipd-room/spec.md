## MODIFIED Requirements

### Requirement: Room docs and registration
id: room-skill-docs
base: 70b8fd78ccfb

The repository SHALL ship the room concept doc and the room how-to, each
passing `docs_lint.py`. `docs/multi-agent-pr.md` SHALL be a `concept` doc
titled `# Multi-agent PR`, at 100 lines or fewer, that names the PR room as
the mechanism and explains: the room as the pull request's comment thread;
the Agent Card and the Message with its task id and state; the six task
states `submitted`, `working`, `input-required`, `completed`, `failed`, and
`canceled`; one hidden marker per comment with prose below; room traffic as
issue comments, except that a review finding's messages reply on the
finding's own review thread and a `completed` reply resolves it; that an
agent acts only on an `input-required` task addressed to it, or unaddressed
and matching a skill on its card, and never on its own last message; the
round cap `room.max_rounds` with its default of 6 and the `failed` state it
posts; and the semantic review gate as the first member, posting each finding
as a task. Its state diagram SHALL label the state `input-required` with that
exact name, and the doc SHALL NOT explain Mermaid syntax or restate a
transition the diagram shows.

The concept doc SHALL follow the main-page shape. Its level-2 headings SHALL
be `## Why a room`, `## The model`, `## Who acts when`,
`## The review gate is the first member`, `## When to use it`,
`## How to run it`, and `## Reference`, in that order, with no `## See also`.
`## When to use it` SHALL say when a pull request needs a room: more than one
agent, or an agent and a person, take turns on it. `## How to run it` SHALL
name the three ways a turn runs — `/s:room` in a developer session, the
Actions wake installed by `shipd copilot add --room`, and `shipd room run` on
a developer machine — SHALL state that the wake acts only on an addressed
task, and SHALL link `room-run.md`. `## Reference` SHALL link `room-run.md`,
`room-wake-reference.md`, `room-review-claims.md`, `agent-identity.md`,
`customise.md`, and `semantic-review.md`.

The room how-to SHALL be `docs/room-run.md`, as `multi-agent-walkthrough-doc`
states it, and `docs/pr-room.md` SHALL NOT exist. The repository SHALL list
`/s:room` in `AGENTS.md`'s skill sentence and the `docs/cheatsheet.md`
command table; `README.md` is not a registration surface. The skill tests SHALL live in
`plugins/s/skills/room/tests/test_room_skill.py`.

#### Scenario: Registration surfaces name the skill
- **WHEN** the room skill test reads `AGENTS.md` and `docs/cheatsheet.md`
- **THEN** each contains `/s:room`

#### Scenario: Doc lints clean
- **WHEN** `docs_lint.py docs/room-run.md` and
  `docs_lint.py docs/multi-agent-pr.md` run
- **THEN** each exits `0`

#### Scenario: Concept doc states the model
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** line 1 is `<!-- doc-type: concept -->`, the title is
  `# Multi-agent PR`, the file is 100 lines or fewer, and its text names
  all six task states, `room.max_rounds`, `/s:room`,
  `shipd copilot add --room`, and `shipd room run`

#### Scenario: Concept doc names the finding thread
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** it says a finding's replies go on its review thread and no
  longer says room traffic uses issue comments only

#### Scenario: Concept doc follows the main-page shape
- **WHEN** the level-2 headings of `docs/multi-agent-pr.md` are listed
- **THEN** they are `## Why a room`, `## The model`, `## Who acts when`,
  `## The review gate is the first member`, `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Concept doc links its neighbours
- **WHEN** the links in `docs/multi-agent-pr.md` are resolved
- **THEN** they include `room-run.md`, `room-wake-reference.md`,
  `room-review-claims.md`, `agent-identity.md`, `customise.md`, and
  `semantic-review.md`, none names `pr-room.md` or
  `multi-agent-autonomous-prs.md`, and every link resolves to a file under
  `docs/`

#### Scenario: How-to links the concept page and the wake
- **WHEN** a reader opens `docs/room-run.md`
- **THEN** its text links `multi-agent-pr.md` and `room-wake-reference.md`,
  and `docs/pr-room.md` does not exist

#### Scenario: Concept doc carries no diagram-syntax note
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** its Mermaid block declares `state "input-required" as input`, and
  the prose outside the block contains neither `input_required` nor the word
  `hyphen`
