# shipd-room

### Requirement: Room skill loop
id: room-skill-loop

The plugin SHALL ship `plugins/s/skills/room/SKILL.md`, invoked as
`/s:room [<pr>]`, whose workflow runs the `shipd room` verbs in this order:
`join` (with `--skill review-finding --skill question --skill status`
unless the user names skills), `list`,
then a foreground `watch <pr> --since <cursor> --timeout 600`; on a surfaced
task it SHALL post `message --task <id> --state working`, do the work, and
post the reply with an explicit `--state` (`completed`, or `input-required`
with `--to` the asker), then re-enter `watch` with the line's `cursor`. The
skill SHALL never act on a task the `watch` output did not surface, and SHALL
resolve the agent name only through the verbs' own resolution, stopping with
the verb's `Error:` text when no name resolves.

#### Scenario: Skill names the loop's verbs in order
- **WHEN** the room skill test reads `plugins/s/skills/room/SKILL.md`
- **THEN** it finds `shipd room join`, `shipd room list`, `shipd room watch`,
  `shipd room message`, and `shipd room close` in that order of first
  appearance, and `--skill review-finding --skill question --skill status`
  and `--timeout 600`

#### Scenario: Reply carries an explicit state
- **WHEN** the room skill test scans the skill's `shipd room message`
  invocations
- **THEN** each one carries a `--state` flag

### Requirement: Room skill stop conditions
id: room-skill-stops

The skill SHALL end its turn and report, without posting, when `watch`
exits `0` with empty stdout (no actionable task, reporting the cursor), when
`message` exits `1` with a round-cap `Error:` line (the verb has already
posted `failed`), or when any verb exits non-zero. The skill SHALL run
`watch` only in the foreground, and SHALL state that a delegated worker never
runs `watch` in the background.

#### Scenario: Skill states every stop
- **WHEN** the room skill test reads the skill
- **THEN** it finds the empty-watch stop, the round-cap stop, and the
  foreground-only rule for `watch`

### Requirement: Room skill posts prose, never code
id: room-skill-no-code

The skill SHALL post prose replies only. It SHALL NOT edit, commit, or push
code while working a task; a task that needs a code change SHALL be answered
with a reply naming `/s:fix` or `/s:plan` as the hand-off. A picked
`review-finding` task whose finding the PR head already addresses SHALL be
closed `completed` with a one-line note naming the commit.

#### Scenario: Skill forbids code edits
- **WHEN** the room skill test reads the skill
- **THEN** it finds the no-code rule naming `/s:fix` and `/s:plan`

### Requirement: Room harness body
id: room-skill-body

The plugin SHALL ship `plugins/s/harness/bodies/room.md`, opening with a
`<!-- description: … -->` marker, and its fallback reference
`plugins/s/harness/references/room.md`. The body SHALL gate the watch loop on
`<!-- if:background-tasks -->`; its `<!-- else -->` segment SHALL run one
`shipd room list <pr> --json` read, report the actionable tasks, and end
without running `watch`.

#### Scenario: Bare harness reads once
- **WHEN** `harness_bodies.render("room", (), refs_dir="R")` runs
- **THEN** the output contains `shipd room list` and no `shipd room watch`

#### Scenario: Background harness watches
- **WHEN** the body renders with `background-tasks` declared
- **THEN** the output contains `shipd room watch` and `--timeout 600`

### Requirement: Room docs and registration
id: room-skill-docs

The change SHALL add `docs/pr-room.md`, a `how-to` doc that passes
`docs_lint.py`, and SHALL list `/s:room` in `AGENTS.md`'s skill sentence, the
`README.md` command tables, and the `docs/cheatsheet.md` command table. The
skill tests SHALL live in `plugins/s/skills/room/tests/test_room_skill.py`,
and the plugin version SHALL advance one patch above `main`'s value.

#### Scenario: Registration surfaces name the skill
- **WHEN** the room skill test reads `AGENTS.md`, `README.md`, and
  `docs/cheatsheet.md`
- **THEN** each contains `/s:room`

#### Scenario: Doc lints clean
- **WHEN** `docs_lint.py docs/pr-room.md` runs
- **THEN** it exits `0`
