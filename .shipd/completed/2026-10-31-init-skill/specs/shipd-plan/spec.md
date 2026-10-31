## MODIFIED Requirements

### Requirement: Missing-layout guard
id: missing-layout-guard
base: 52592b01ec26
Dropped: Missing layout stops the flow
Dropped: Accepted scaffold proceeds through the engine

The skill SHALL run the shared needs-setup check
(`skills/init/references/needs-setup.md`) inside the change's worktree before
investigating, and SHALL act on the `action:` line of `spec_status.py
init-status`: on `none` it SHALL continue; on `scaffold` it SHALL create the
layout through `spec_status.py init`, print one line, and continue; on
`wizard` it SHALL run the `/s:init` wizard and then continue. It SHALL NOT
create the directories by hand and SHALL NOT continue planning as though a
missing layout existed.

#### Scenario: Layout-missing repo is scaffolded silently
- **GIVEN** a repository whose `.shipd-config.json` declares `"pr-mode":
  "draft"` and which has no content directory
- **WHEN** `/s:plan` runs
- **THEN** the skill runs `spec_status.py init`, prints one line naming the
  created layout, asks no setup question, and continues planning

#### Scenario: First run opens the wizard, then planning continues
- **GIVEN** a repository with no `.shipd-config.json` and no content directory
- **WHEN** `/s:plan` runs with a human present
- **THEN** the `/s:init` wizard runs first and planning continues after it

#### Scenario: Unattended first run never asks
- **GIVEN** the same first-run repository and an invocation that says no human
  is available
- **WHEN** `/s:plan` runs
- **THEN** the check passes `--unattended`, the action is `scaffold`, and no
  dialog opens
