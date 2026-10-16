## MODIFIED Requirements

### Requirement: Room skill stop conditions
id: room-skill-stops
base: 5626f970d47b

The skill SHALL end its turn and report, without posting, when `watch`
prints a `closed` line (the pull request was merged or closed), when `watch`
exits `0` with empty stdout and the skill was not invoked with `stay` (no
actionable task, reporting the cursor), when `message` exits `1` with a
round-cap `Error:` line (the verb has already posted `failed`), or when any
verb exits non-zero. On a `closed` line whose `open` array is not empty, the
report SHALL list those tasks as unresolved, with each id and state. The
skill SHALL pass the pull request URL, or `--repo` when the user names a
repository, to every verb, and SHALL run `watch` only in the foreground, and
SHALL state that a delegated worker never runs `watch` in the background.

#### Scenario: Skill states every stop
- **WHEN** the room skill test reads the skill
- **THEN** it finds the closed-room stop, the empty-watch stop scoped to a
  turn without `stay`, the round-cap stop, and the foreground-only rule for
  `watch`

#### Scenario: Skill reports unresolved tasks on a closed room
- **WHEN** the room skill test reads the skill
- **THEN** it finds the `open` array of the `closed` line and the word
  `unresolved`

#### Scenario: Skill passes the repository through
- **WHEN** the room skill test reads the skill
- **THEN** it finds `--repo` and the pull request URL named as what every
  verb receives

## ADDED Requirements

### Requirement: The reviewer merges only from a clear room
id: room-skill-merge-rule

Before it runs `gh pr merge`, with or without `--auto`, an agent whose card
role is `reviewer` SHALL run `shipd room list <pr> --open --json`. If the
`tasks` array is not empty, then the agent SHALL NOT merge: with `stay` it
SHALL keep watching, and without `stay` it SHALL report the open tasks and
end the turn. The harness body and reference SHALL carry the same rule.

#### Scenario: Skill states the merge rule
- **WHEN** the room skill test reads the skill
- **THEN** it finds `gh pr merge`, `list <pr> --open`, `reviewer`, and
  `working` and `input-required`

#### Scenario: Harness body carries the rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",),
  refs_dir="R")` runs
- **THEN** the output names `--open` and `gh pr merge`
