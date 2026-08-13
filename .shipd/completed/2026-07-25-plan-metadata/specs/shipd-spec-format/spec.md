## ADDED Requirements

### Requirement: Plan header metadata lines
id: plan-header-metadata-lines

A change's `plan.md` MAY carry a metadata block: contiguous `<Key>: <value>`
lines immediately following the `Status:` line, ended by the first blank line
or heading. Tooling SHALL recognize exactly four keys — `Profile`, `Epic`,
`Initiative`, `Theme` — and every value SHALL be a kebab-case slug. The block
SHALL be optional: a plan whose header carries only the title and `Status:`
line SHALL remain valid.

#### Scenario: Metadata block is parsed
- **WHEN** a plan header reads `# csv-export`, `Status: draft`,
  `Theme: reliability`, `Epic: reporting-overhaul` on consecutive lines
- **THEN** tooling parses `Theme` and `Epic` as the change's metadata

#### Scenario: Metadata-free header stays valid
- **WHEN** a plan header carries only the title and `Status:` line
- **THEN** the plan is treated exactly as before this feature existed

### Requirement: Plan profile values
id: plan-profile-values

The `Profile:` metadata key SHALL accept exactly `full` or `lite`, and an
absent `Profile:` line SHALL mean `full`. The `lite` profile SHALL relax
content expectations only (brevity, optional test-first ordering); it SHALL
NOT change the required artifact set or any structural lint rule — every
change carries `plan.md`, delta specs, and `tasks.md` regardless of profile.

#### Scenario: Absent profile defaults to full
- **WHEN** a plan carries no `Profile:` line
- **THEN** tooling treats the change as `full` profile

#### Scenario: Lite keeps the artifact set
- **WHEN** a change's plan carries `Profile: lite`
- **THEN** the change still requires `plan.md`, at least one delta spec, and
  `tasks.md`, and structural lint rules apply unchanged

### Requirement: Initiative attaches through the epic
id: initiative-attaches-through-epic

If a change's plan carries an `Epic:` line, then the plan SHALL NOT also
carry an `Initiative:` line — a grouped change derives its initiative through
its epic. Where a change belongs to no epic, it MAY carry an `Initiative:`
line directly.

#### Scenario: Epic and initiative together are invalid
- **WHEN** a plan carries both `Epic: reporting-overhaul` and
  `Initiative: mvp-readiness`
- **THEN** tooling treats the plan as invalid and points at the epic as the
  place to attach the initiative

#### Scenario: Standalone change may carry an initiative
- **WHEN** a plan with no `Epic:` line carries `Initiative: mvp-readiness`
- **THEN** the plan is valid

### Requirement: Theme vocabulary config
id: theme-vocabulary-config

The system SHALL reserve `am/config.json` as optional, stdlib-JSON repo
configuration. When the file exists and holds a non-empty `valid_themes`
array, a plan's `Theme:` value SHALL be validated against that vocabulary.
When the file is absent or declares no `valid_themes`, any kebab-case theme
SHALL be accepted. If the file exists but is not valid JSON, tooling SHALL
report an error naming the file.

#### Scenario: Theme outside the vocabulary is invalid
- **GIVEN** `am/config.json` declares `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: developer-experience`
- **THEN** tooling reports the theme as outside the vocabulary

#### Scenario: No config accepts any kebab theme
- **WHEN** no `am/config.json` exists and a plan carries `Theme: any-label`
- **THEN** the theme is accepted

#### Scenario: Malformed config is an error
- **WHEN** `am/config.json` exists but is not parseable JSON
- **THEN** tooling reports an error naming `am/config.json`
