# shipd-initiative

### Requirement: Initiative workflow skill
id: initiative-workflow-skill

An `/s:initiative` skill SHALL provide, selected by argument: `new <slug>`
— a workspace-first interview (existing briefs and declared project slugs
read via the engine's show and `cat` verbs before asking; one batched
question round for the goal, outcome requirements, and optional `Project:`
scope) that authors the brief in a staging area and installs it at
`Status: open` through `spec_emit.py initiative <slug> --from <file>` (no
PR — briefs live outside the repo, and the skill SHALL NOT construct the
brief's path or write it directly); `list` — every initiative's status,
requirement progress, and project scope via the status CLI; and
`review <slug>` — walking the brief's requirements with the user, ticking
outcomes the user confirms achieved, then running `initiative-sync`. When
no workspace root is discoverable, every verb SHALL stop with the CLI's
no-workspace error rather than inventing a location, and SHALL point the
user at `/s:workspace init` as the setup path.

#### Scenario: New emits a lint-clean open brief through the engine
- **WHEN** the skill's `new` verb completes for `mvp-readiness`
- **THEN** the brief was installed via `spec_emit.py initiative`, exists
  with `Status: open` and outcome checkboxes at the workspace's resolved
  brief path, and `--initiative mvp-readiness` exits zero

#### Scenario: No workspace stops the skill and names the remedy
- **WHEN** any verb runs where no workspace root is discoverable
- **THEN** the skill reports the no-workspace error, writes nothing, and
  points the user at `/s:workspace init`

### Requirement: Initiative attachment to epics
id: initiative-attachment

The skill's `set <epic> <initiative>` verb SHALL tag an epic with exactly
one initiative by driving the status CLI's `epic-set-initiative` verb —
never editing the epic file by hand — and SHALL ship the edit through the
repository's worktree-and-PR workflow (never a direct commit to main),
verifying with the linter's `--epic` mode that the epic and the initiative
reference are valid before shipping. Asked to attach an initiative to a
change that carries `Epic:`, the skill SHALL refuse and point at the epic
as the attachment point.

#### Scenario: Set tags the epic through the engine and ships a PR
- **WHEN** `set workspace-projects mvp-readiness` completes
- **THEN** `epic-set-initiative` wrote the single `Initiative:` header
  line, the edit arrives on main via an auto-merging PR, and
  `--epic workspace-projects` exits zero

#### Scenario: Change with an epic is refused
- **WHEN** the user asks to attach an initiative to a change whose plan
  carries `Epic:`
- **THEN** the skill refuses and names the epic to tag instead
