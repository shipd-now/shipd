## MODIFIED Requirements

### Requirement: Epic artifact layout
id: epic-artifact-layout
base: b29b8c90ab0a

An epic SHALL live at `<content-dir>/epics/<slug>/epic.md` (default
`.shipd/epics/<slug>/epic.md`), beginning with a `# <slug>` title matching its
directory, a `Status:` line whose value is one of `draft`, `ready`,
`active`, `complete`, and optionally a header metadata block. The document
SHALL carry `## Introduction`, `## Decisions`, `## Design`, and `## Changes`
sections, and `## Introduction` SHALL be the first level-2 section. The
Introduction SHALL open with the problem and its motivation before
describing the feature and its intended outcome, with success criteria
recommended, and SHALL include a `### Non-goals` subsection listing the
scope exclusions. `## Changes` SHALL hold a stub table whose header is
either the exact columns
`| Change | Description | Code | Integration | Unknowns | Risk |` or those
six followed by `| After |`, at least one data row, kebab-case change slugs
unique within the table, and every rating cell one of `low`, `medium`,
`high`. Where the `After` column is present, each `After` cell SHALL be
empty or a comma-separated list of kebab-case slugs, each naming another
row of the same table, declaring the members this member must be planned
after; the column binds planning order only, never build order.

#### Scenario: Conforming epic is valid at the new path
- **WHEN** `.shipd/epics/reporting-overhaul/epic.md` starts with
  `# reporting-overhaul`, `Status: draft`, opens with an `## Introduction`
  carrying a `### Non-goals` subsection, carries `## Decisions`,
  `## Design`, and `## Changes`, and its stub table lists `csv-export` with
  ratings `low`/`medium`/`low`/`low`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Missing introduction is rejected
- **WHEN** an epic carries `## Decisions`, `## Design`, and `## Changes`
  but no `## Introduction` section
- **THEN** tooling reports the missing section

#### Scenario: Invalid rating is rejected
- **WHEN** a stub row's Risk cell reads `huge`
- **THEN** tooling reports the invalid rating

#### Scenario: After column is accepted
- **WHEN** a stub table's header carries the six columns followed by
  `After`, and row `csv-import` holds `csv-export` in its `After` cell
- **THEN** tooling accepts the epic and reads `csv-import` as planned after
  `csv-export`

#### Scenario: After names an unknown member
- **WHEN** a row's `After` cell names `no-such-member`
- **THEN** tooling reports the unknown slug
