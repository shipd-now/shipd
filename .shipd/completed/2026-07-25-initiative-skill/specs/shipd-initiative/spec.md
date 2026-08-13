## ADDED Requirements

### Requirement: Initiative workflow skill
id: initiative-workflow-skill

An `/s:initiative` skill SHALL provide, selected by argument: `new <slug>` —
a workspace-first interview (existing briefs and declared project slugs read
before asking; one batched question round for the goal, outcome
requirements, and optional `Project:` scope) that writes a brief at
`Status: open` directly to `<workspace-root>/initiatives/<slug>/brief.md`
(no PR — briefs live outside the repo) and lints it with the linter's
`--initiative` mode before finishing; `list` — every initiative's status,
requirement progress, and project scope via the status CLI; and
`review <slug>` — walking the brief's requirements with the user, ticking
outcomes the user confirms achieved, then running `initiative-sync`. When no
workspace root is discoverable, every verb SHALL stop with the CLI's
no-workspace error rather than inventing a location.

#### Scenario: New emits a lint-clean open brief
- **WHEN** the skill's `new` verb completes for `mvp-readiness`
- **THEN** `<ws>/initiatives/mvp-readiness/brief.md` exists with
  `Status: open` and outcome checkboxes, and `--initiative mvp-readiness`
  exits zero

#### Scenario: Review ticks outcomes and syncs
- **WHEN** the user confirms the final open requirement during `review`
- **THEN** the checkbox is ticked and `initiative-sync` runs, deriving
  `achieved`

#### Scenario: No workspace stops the skill
- **WHEN** any verb runs where no workspace root is discoverable
- **THEN** the skill reports the no-workspace error and writes nothing

### Requirement: Initiative attachment to epics
id: initiative-attachment

The skill's `set <epic> <initiative>` verb SHALL tag an epic with exactly
one initiative by writing the `Initiative:` header line in
`am/epics/<epic>/epic.md`, replacing any existing `Initiative:` line, and
SHALL ship the edit through the repository's worktree-and-PR workflow
(never a direct commit to main), verifying with the linter's `--epic` mode
that the epic and the initiative reference are valid before shipping. Asked
to attach an initiative to a change that carries `Epic:`, the skill SHALL
refuse and point at the epic as the attachment point.

#### Scenario: Set tags the epic and ships a PR
- **WHEN** `set workspace-projects mvp-readiness` completes
- **THEN** the epic's header carries `Initiative: mvp-readiness`, the edit
  arrives on main via an auto-merging PR, and `--epic workspace-projects`
  exits zero

#### Scenario: Change with an epic is refused
- **WHEN** the user asks to attach an initiative to a change whose plan
  carries `Epic:`
- **THEN** the skill refuses and names the epic to tag instead
