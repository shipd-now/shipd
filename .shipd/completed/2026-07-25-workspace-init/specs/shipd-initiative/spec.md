## MODIFIED Requirements

### Requirement: Initiative workflow skill
id: initiative-workflow-skill
base: 3d37121e0d77

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
no-workspace error rather than inventing a location, and SHALL point the
user at `/s:workspace init` as the setup path.

#### Scenario: New emits a lint-clean open brief
- **WHEN** the skill's `new` verb completes for `mvp-readiness`
- **THEN** `<ws>/initiatives/mvp-readiness/brief.md` exists with
  `Status: open` and outcome checkboxes, and `--initiative mvp-readiness`
  exits zero

#### Scenario: Review ticks outcomes and syncs
- **WHEN** the user confirms the final open requirement during `review`
- **THEN** the checkbox is ticked and `initiative-sync` runs, deriving
  `achieved`

#### Scenario: No workspace stops the skill and names the remedy
- **WHEN** any verb runs where no workspace root is discoverable
- **THEN** the skill reports the no-workspace error, writes nothing, and
  points the user at `/s:workspace init`
