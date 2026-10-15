## MODIFIED Requirements

### Requirement: Plan header metadata lines
id: plan-header-metadata-lines
base: e2fd4dd62f30

A change's `plan.md` MAY carry a metadata block: contiguous `<Key>: <value>`
lines immediately following the `Status:` line, ended by the first blank line
or heading, where a key is a bareword of letters, digits, and hyphens. Tooling
SHALL recognize exactly seven keys — `Profile`, `Epic`, `Initiative`, `Theme`,
`Fixes`, `Planned-at`, `Gated-hash`. The first five SHALL take kebab-case
slug values; `Planned-at` SHALL take a 7–40 character lowercase hex commit id
and `Gated-hash` a 12-character lowercase hex content hash, both written by
the context gate on a passing run and preserved by every status write. The
`Fixes` key SHALL be repeatable, each line naming one shipped change this
change remediates (the post-merge fix linkage the delivery-metrics
change-failure signal derives from); tooling SHALL NOT require the named slug
to resolve to an existing change. The block SHALL be optional: a plan whose
header carries only the title and `Status:` line SHALL remain valid.

#### Scenario: Metadata block is parsed
- **WHEN** a plan header reads `# csv-export`, `Status: draft`,
  `Theme: reliability`, `Epic: reporting-overhaul` on consecutive lines
- **THEN** tooling parses `Theme` and `Epic` as the change's metadata

#### Scenario: Stamp lines are parsed as metadata
- **WHEN** a plan header carries `Status: ready`, `Epic: reporting-overhaul`,
  `Planned-at: 076a9effc1acd6acbf99b2c2209d1998fe5ab9fe`,
  `Gated-hash: 9851e28d228d` on consecutive lines
- **THEN** tooling parses all three pairs, and `show` prints the two stamp
  lines alongside the epic

#### Scenario: Fixes lines are parsed and repeatable
- **WHEN** a plan header carries `Status: draft` followed by
  `Fixes: board-theme` and `Fixes: board-search` on consecutive lines
- **THEN** tooling parses both slugs as changes this plan remediates, while a
  non-kebab `Fixes` value is a lint error

#### Scenario: Metadata-free header stays valid
- **WHEN** a plan header carries only the title and `Status:` line
- **THEN** the plan is treated exactly as before this feature existed
