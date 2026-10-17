## MODIFIED Requirements

### Requirement: Room skill loop
id: room-skill-loop
base: 5dc2e214af13

The plugin SHALL ship `plugins/s/skills/room/SKILL.md`, invoked as
`/s:room [<pr>] [stay]`, whose workflow runs the `shipd room` verbs in this
order: `join` (with `--skill review-finding --skill question --skill status`
unless the user names skills), `list`,
then a foreground `watch <pr> --since <cursor> --timeout 540`; on a surfaced
task it SHALL post `message --task <id> --state working`, do the work, and
post the reply with an explicit `--state` (`completed`, or `input-required`
with `--to` the asker), then re-enter `watch` with the line's `cursor`. With
`stay`, an empty wait SHALL re-enter `watch` with the cursor `watch` printed
on stderr instead of ending the turn, each `watch` call still running in the
foreground with `--timeout 540`. The skill SHALL state that the tool call
running `watch` carries its own timeout above 540 seconds, so the harness
never backgrounds the wait, and SHALL name `--timeout 600` nowhere. The skill
SHALL never act on a task the `watch` output did not surface, and SHALL
resolve the agent name only through the verbs' own resolution, stopping with
the verb's `Error:` text when no name resolves.

#### Scenario: Skill names the loop's verbs in order
- **WHEN** the room skill test reads `plugins/s/skills/room/SKILL.md`
- **THEN** it finds `shipd room join`, `shipd room list`, `shipd room watch`,
  `shipd room message`, and `shipd room close` in that order of first
  appearance, and `--skill review-finding --skill question --skill status`
  and `--timeout 540`, and no `--timeout 600`

#### Scenario: Skill states the tool-call timeout
- **WHEN** the room skill test reads the skill
- **THEN** it finds the rule that the tool call's own timeout exceeds 540
  seconds, and `600000`

#### Scenario: Reply carries an explicit state
- **WHEN** the room skill test scans the skill's `shipd room message`
  invocations
- **THEN** each one carries a `--state` flag

#### Scenario: Skill documents stay mode
- **WHEN** the room skill test reads the skill
- **THEN** it finds `/s:room [<pr>] [stay]` and the rule that a `stay` turn
  re-enters `watch` after an empty wait

### Requirement: Room harness body
id: room-skill-body
base: cd149a1fd79c

The plugin SHALL ship `plugins/s/harness/bodies/room.md`, opening with a
`<!-- description: … -->` marker, and its fallback reference
`plugins/s/harness/references/room.md`. The body SHALL gate the watch loop on
`<!-- if:background-tasks -->`; its `<!-- else -->` segment SHALL run one
`shipd room list <pr> --json` read, report the actionable tasks, and end
without running `watch`. The body's watch step and the reference's watch
section SHALL name `--timeout 540`, never `--timeout 600`, and SHALL state
that the tool call's own timeout must exceed 540 seconds. `docs/pr-room.md`
SHALL name `--timeout 540` wherever it shows the watch wait.

#### Scenario: Bare harness reads once
- **WHEN** `harness_bodies.render("room", (), refs_dir="R")` runs
- **THEN** the output contains `shipd room list` and no `shipd room watch`

#### Scenario: Background harness watches
- **WHEN** the body renders with `background-tasks` declared
- **THEN** the output contains `shipd room watch`, `--timeout 540`, and
  `540 seconds`, and no `--timeout 600`

#### Scenario: Reference and how-to name the new timeout
- **WHEN** the room skill test reads `plugins/s/harness/references/room.md`
  and `docs/pr-room.md`
- **THEN** each contains `--timeout 540` and no `--timeout 600`
