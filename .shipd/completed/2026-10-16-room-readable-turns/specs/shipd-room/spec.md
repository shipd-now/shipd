## MODIFIED Requirements

### Requirement: Room skill loop
id: room-skill-loop
base: 1bb3c42ea4fc

The plugin SHALL ship `plugins/s/skills/room/SKILL.md`, invoked as
`/s:room [<pr>] [stay]`, whose workflow runs the `shipd room` verbs in this
order: `join` (with `--skill review-finding --skill question --skill status`
unless the user names skills), `list`,
then a foreground `watch <pr> --since <cursor> --timeout 600`; on a surfaced
task it SHALL post `message --task <id> --state working`, do the work, and
post the reply with an explicit `--state` (`completed`, or `input-required`
with `--to` the asker), then re-enter `watch` with the line's `cursor`. With
`stay`, an empty wait SHALL re-enter `watch` with the cursor `watch` printed
on stderr instead of ending the turn, each `watch` call still running in the
foreground with `--timeout 600`. The skill SHALL never act on a task the
`watch` output did not surface, and SHALL resolve the agent name only through
the verbs' own resolution, stopping with the verb's `Error:` text when no
name resolves.

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

#### Scenario: Skill documents stay mode
- **WHEN** the room skill test reads the skill
- **THEN** it finds `/s:room [<pr>] [stay]` and the rule that a `stay` turn
  re-enters `watch` after an empty wait

### Requirement: Room skill stop conditions
id: room-skill-stops
base: ce7a0352ba6e

The skill SHALL end its turn and report, without posting, when `watch`
prints a `closed` line (the pull request was merged or closed), when `watch`
exits `0` with empty stdout and the skill was not invoked with `stay` (no
actionable task, reporting the cursor), when `message` exits `1` with a
round-cap `Error:` line (the verb has already posted `failed`), or when any
verb exits non-zero. The skill SHALL run `watch` only in the foreground, and
SHALL state that a delegated worker never runs `watch` in the background.

#### Scenario: Skill states every stop
- **WHEN** the room skill test reads the skill
- **THEN** it finds the closed-room stop, the empty-watch stop scoped to a
  turn without `stay`, the round-cap stop, and the foreground-only rule for
  `watch`
