## ADDED Requirements

### Requirement: Epic token breakdown aggregation
id: epic-token-breakdown

When `epic-sync` runs on a non-draft epic, it SHALL also rewrite the epic
file's trailing `## Token usage breakdown` section: a
`Tool | Calls | Output tokens` markdown table (rows sorted by output tokens
descending, a bold `**Total**` row) summing, per tool, the
`## Token usage breakdown` tables found in the epic's members' archived
`tasks.md` files — each member resolved the way the status derivation
already resolves member state, a member with no archived table or an
unparseable one contributing nothing. The rewrite SHALL be idempotent
(replacing an existing section, preserving all other content), and if no
member carries a table, then the epic SHALL end with no
`## Token usage breakdown` section (an existing one removed). The draft-epic
guard is unchanged: a draft epic's file is never touched.

#### Scenario: Member tables sum into the epic table
- **WHEN** `epic-sync` runs on an epic with two archived members whose
  `tasks.md` tables each show `Bash` with 100 output tokens and one call
- **THEN** the epic's trailing section shows a `Bash` row with 200 output
  tokens and 2 calls, and a `**Total**` row of 200

#### Scenario: A re-run is idempotent
- **WHEN** `epic-sync` runs twice with unchanged members
- **THEN** the second run leaves the epic file byte-identical

#### Scenario: A member without a table contributes nothing
- **WHEN** one member's archived `tasks.md` has no breakdown section
- **THEN** the epic table sums only the other members' tables and the sync
  raises no error

#### Scenario: No member tables, no epic section
- **WHEN** no member's archived `tasks.md` carries a breakdown table
- **THEN** the synced epic file carries no `## Token usage breakdown`
  section, even if one existed before

#### Scenario: A draft epic is untouched
- **WHEN** `epic-sync` runs on a `draft` epic
- **THEN** the epic file is not modified
