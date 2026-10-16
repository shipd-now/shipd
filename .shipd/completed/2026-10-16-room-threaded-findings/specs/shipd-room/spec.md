## MODIFIED Requirements

### Requirement: Room skill posts prose, and only the author's agent fixes findings
id: room-skill-no-code
base: f275dad071e2

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

### Requirement: Room docs and registration
id: room-skill-docs
base: 06503f4836a1

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
