# shipd-room

### Requirement: Room skill loop
id: room-skill-loop

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

### Requirement: Room skill stop conditions
id: room-skill-stops

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

### Requirement: Room skill posts prose, and only the author's agent fixes findings
id: room-skill-no-code

The skill SHALL read the agent's role as the `role` on its own card in
`shipd room list <pr> --json`. While working a surfaced `review-finding`
task, an agent whose role is `author` MAY edit, commit, and push code, only
when the working tree is on the pull request's head branch (`gh pr view
<pr> --json headRefName` equals `git branch --show-current`) and is clean:
it SHALL make the smallest change that addresses the finding, run the tests
covering the touched files, commit, push with plain `git push` and never
with `--force`, and close the task `completed` naming the commit's short
SHA. If any of those checks or the test run fails, then it SHALL push
nothing and fall back to the prose hand-off. Every other role, and every
task that is not a `review-finding`, SHALL post prose only and never edit,
commit, or push code; a task that needs a code change SHALL be answered with
a reply naming `/s:fix` or `/s:plan` as the hand-off. No agent SHALL push to
a branch other than its own pull request's head branch. A picked
`review-finding` task whose finding the PR head already addresses SHALL be
closed `completed` with a one-line note naming the commit.

#### Scenario: Skill forbids code edits
- **WHEN** the room skill test reads the skill
- **THEN** it finds the no-code rule naming `/s:fix` and `/s:plan`, and the
  text `never edits, commits, or pushes code`

#### Scenario: Skill states the author's fix rule and its guard
- **WHEN** the room skill test reads the skill
- **THEN** it finds `author`, `review-finding`, `headRefName`, `git push`,
  and the rule never to push with `--force`

#### Scenario: Harness body carries the same rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",),
  refs_dir="R")` runs
- **THEN** the output names `author`, `headRefName`, `/s:fix`, and `/s:plan`

### Requirement: Room harness body
id: room-skill-body

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

### Requirement: Room docs and registration
id: room-skill-docs

The repository SHALL ship two room docs that pass `docs_lint.py`.
`docs/multi-agent-pr.md` SHALL be a `concept` doc titled `# Multi-agent PR`,
at 100 lines or fewer, that names the PR room as the mechanism and explains:
the room as the pull request's comment thread; the Agent Card and the Message
with its task id and state; the six task states `submitted`, `working`,
`input-required`, `completed`, `failed`, and `canceled`; one hidden marker
per comment with prose below; room traffic as issue comments, except that a
review finding's messages reply on the finding's own review thread and a
`completed` reply resolves it; that an
agent acts only on an `input-required` task addressed to it, or unaddressed
and matching a skill on its card, and never on its own last message; the
round cap `room.max_rounds` with its default of 6 and the `failed` state it
posts; the two ways a turn runs, `/s:room` in a developer session and the
Actions wake installed by `shipd copilot add --room`; and the semantic review
gate as the first member, posting each finding as a task. It SHALL link
`docs/pr-room.md`, `docs/room-wake-reference.md`, `docs/customise.md`, and
`docs/semantic-review.md`. `docs/pr-room.md` SHALL be a `how-to` doc titled
`# Run an agent's turn in a multi-agent PR` that links
`docs/multi-agent-pr.md` and `docs/room-wake-reference.md`, and SHALL state
that only an agent with role `author` commits a finding's fix to its own
pull request while every other role answers in prose. The repository
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

#### Scenario: Concept doc names the finding thread
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** it says a finding's replies go on its review thread and no
  longer says room traffic uses issue comments only

#### Scenario: Concept doc links its neighbours
- **WHEN** the links in `docs/multi-agent-pr.md` are resolved
- **THEN** they include `pr-room.md`, `room-wake-reference.md`,
  `customise.md`, and `semantic-review.md`, and every link resolves to a
  file under `docs/`

#### Scenario: How-to links the concept page and the wake
- **WHEN** a reader opens `docs/pr-room.md`
- **THEN** its title is `# Run an agent's turn in a multi-agent PR` and its
  text links `multi-agent-pr.md` and `room-wake-reference.md`

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
