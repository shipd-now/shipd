## ADDED Requirements

### Requirement: Plugin-shipped PRD template files
id: prd-template-files

The plugin SHALL ship one PRD template per tier at
`plugins/s/skills/prd/references/<tier>.md` (`basic.md`, `standard.md`,
`comprehensive.md`). Each template SHALL open with a `# ` title placeholder
line, carry `Status: draft` and a `Template:` line naming its own tier, and
present exactly its tier's required sections from the engine registry as
level-2 headings in registry order — no missing sections and no extra
sections in the skeleton — each followed by guidance prose an authored PRD
replaces. A test suite SHALL guard the templates against registry drift:
heading equality per tier, the `Template:` line, the header shape, and the
absence of unexpected template files, and SHALL verify a PRD filled from a
template passes the engine's PRD validation.

#### Scenario: Templates exist per tier
- **WHEN** the plugin tree is inspected
- **THEN** `plugins/s/skills/prd/references/` holds exactly `basic.md`,
  `standard.md`, and `comprehensive.md`

#### Scenario: Skeleton headings equal the registry
- **WHEN** a template's level-2 headings are compared with its tier's
  registry tuple
- **THEN** they are equal in content and order

#### Scenario: Template names its own tier
- **WHEN** `standard.md` is read
- **THEN** its header carries `Template: standard` and `Status: draft`

#### Scenario: Registry drift fails the guard
- **WHEN** the registry and a template skeleton disagree on a section
- **THEN** the drift-guard test fails naming the tier

#### Scenario: A filled template lints clean
- **WHEN** a PRD is produced from the `basic` template by replacing the
  title placeholder and guidance prose
- **THEN** the engine's PRD validation reports no errors
