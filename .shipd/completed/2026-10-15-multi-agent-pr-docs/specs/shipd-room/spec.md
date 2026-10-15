## MODIFIED Requirements

### Requirement: Room docs and registration
id: room-skill-docs
base: 984ee6e6efac

The repository SHALL ship two room docs that pass `docs_lint.py`.
`docs/multi-agent-pr.md` SHALL be a `concept` doc titled `# Multi-agent PR`,
at 100 lines or fewer, that names the PR room as the mechanism and explains:
the room as the pull request's comment thread; the Agent Card and the Message
with its task id and state; the six task states `submitted`, `working`,
`input-required`, `completed`, `failed`, and `canceled`; one hidden marker
per comment with prose below; room traffic as issue comments only; that an
agent acts only on an `input-required` task addressed to it, or unaddressed
and matching a skill on its card, and never on its own last message; the
round cap `room.max_rounds` with its default of 6 and the `failed` state it
posts; the two ways a turn runs, `/s:room` in a developer session and the
Actions wake installed by `shipd copilot add --room`; and the semantic review
gate as the first member, posting each finding as a task. It SHALL link
`docs/pr-room.md`, `docs/room-wake-reference.md`, `docs/customise.md`, and
`docs/semantic-review.md`. `docs/pr-room.md` SHALL be a `how-to` doc titled
`# Run an agent's turn in a multi-agent PR` that links
`docs/multi-agent-pr.md` and `docs/room-wake-reference.md`. The repository
SHALL list `/s:room` in `AGENTS.md`'s skill sentence, the `README.md`
command tables, and the `docs/cheatsheet.md` command table. The skill tests
SHALL live in `plugins/s/skills/room/tests/test_room_skill.py`.

#### Scenario: Registration surfaces name the skill
- **WHEN** the room skill test reads `AGENTS.md`, `README.md`, and
  `docs/cheatsheet.md`
- **THEN** each contains `/s:room`

#### Scenario: Doc lints clean
- **WHEN** `docs_lint.py docs/pr-room.md` and
  `docs_lint.py docs/multi-agent-pr.md` run
- **THEN** each exits `0`

#### Scenario: Concept doc states the model
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** line 1 is `<!-- doc-type: concept -->`, the title is
  `# Multi-agent PR`, the file is 100 lines or fewer, and its text names
  all six task states, `room.max_rounds`, `/s:room`, and
  `shipd copilot add --room`

#### Scenario: Concept doc links its neighbours
- **WHEN** the links in `docs/multi-agent-pr.md` are resolved
- **THEN** they include `pr-room.md`, `room-wake-reference.md`,
  `customise.md`, and `semantic-review.md`, and every link resolves to a
  file under `docs/`

#### Scenario: How-to links the concept page and the wake
- **WHEN** a reader opens `docs/pr-room.md`
- **THEN** its title is `# Run an agent's turn in a multi-agent PR` and its
  text links `multi-agent-pr.md` and `room-wake-reference.md`
