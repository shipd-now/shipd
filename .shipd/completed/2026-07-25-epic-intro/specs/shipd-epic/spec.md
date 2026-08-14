## MODIFIED Requirements

### Requirement: Epic interview skill
id: epic-interview-skill
base: f225fbf10d1d

An `/s:epic` skill SHALL create an epic by investigating the codebase first,
asking only genuinely un-inferrable decisions in a single batched question
round, and authoring the epic in reader order: an `## Introduction` opening
with the problem and motivation, then the feature and its intended outcome
with success criteria, closing with `### Non-goals`; then the epic's
Decisions and Design sections; then the `## Changes` stub table with
per-change complexity ratings. It SHALL emit the epic at `Status: draft`,
lint it with the linter's single-epic mode, and promote it to `ready` via
`epic-set-status` only on user approval. It SHALL ship the epic through the
repository's worktree-and-PR workflow, and SHALL NOT create member changes —
it points the user at `/s:plan` per stub, whose emitted changes carry
`Epic: <slug>`.

#### Scenario: Epic opens with the why
- **WHEN** the skill authors an epic
- **THEN** the emitted document's first level-2 section is `## Introduction`,
  stating the problem before the feature description, and it contains a
  `### Non-goals` subsection

#### Scenario: Epic emission is draft until approved
- **WHEN** the skill finishes authoring an epic
- **THEN** `am/epics/<slug>/epic.md` carries `Status: draft` until the user
  approves, at which point the skill promotes it to `ready`

#### Scenario: Member changes are not created by the skill
- **WHEN** the skill completes an epic with three stub rows
- **THEN** `am/planned/` gains no new change directories, and the user is
  pointed at `/s:plan` for each stub

#### Scenario: Emitted epics lint clean
- **WHEN** the skill hands off an epic
- **THEN** the linter's single-epic mode exits zero for it
