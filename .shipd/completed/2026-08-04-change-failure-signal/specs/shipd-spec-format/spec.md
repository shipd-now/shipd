## MODIFIED Requirements

### Requirement: Plan header metadata lines
id: plan-header-metadata-lines
base: 0363b2a53aa8

A change's `plan.md` MAY carry a metadata block: contiguous `<Key>: <value>`
lines immediately following the `Status:` line, ended by the first blank line
or heading. Tooling SHALL recognize exactly five keys — `Profile`, `Epic`,
`Initiative`, `Theme`, `Fixes` — and every value SHALL be a kebab-case slug.
The `Fixes` key SHALL be repeatable, each line naming one shipped change this
change remediates (the post-merge fix linkage the delivery-metrics
change-failure signal derives from); tooling SHALL NOT require the named slug
to resolve to an existing change. The block SHALL be optional: a plan whose
header carries only the title and `Status:` line SHALL remain valid.

#### Scenario: Metadata block is parsed
- **WHEN** a plan header reads `# csv-export`, `Status: draft`,
  `Theme: reliability`, `Epic: reporting-overhaul` on consecutive lines
- **THEN** tooling parses `Theme` and `Epic` as the change's metadata

#### Scenario: Fixes lines are parsed and repeatable
- **WHEN** a plan header carries `Status: draft` followed by
  `Fixes: board-theme` and `Fixes: board-search` on consecutive lines
- **THEN** tooling parses both slugs as changes this plan remediates, while a
  non-kebab `Fixes` value is a lint error

#### Scenario: Metadata-free header stays valid
- **WHEN** a plan header carries only the title and `Status:` line
- **THEN** the plan is treated exactly as before this feature existed
