## MODIFIED Requirements

### Requirement: Epic artifact layout
id: epic-artifact-layout
base: 5f5e586822ae

An epic SHALL live at `am/epics/<slug>/epic.md`, beginning with a `# <slug>`
title matching its directory, a `Status:` line whose value is one of `draft`,
`ready`, `active`, `complete`, and optionally a header metadata block. The
document SHALL carry `## Introduction`, `## Decisions`, `## Design`, and
`## Changes` sections, and `## Introduction` SHALL be the first level-2
section. The Introduction SHALL open with the problem and its motivation (the
why) before describing the feature (the what) and its intended outcome, with
success criteria recommended, and SHALL include a `### Non-goals` subsection
listing the scope exclusions. `## Changes` SHALL hold a stub table with the
exact columns `| Change | Description | Code | Integration | Unknowns |
Risk |`, at least one data row, kebab-case change slugs unique within the
table, and every rating cell one of `low`, `medium`, `high`.

#### Scenario: Conforming epic is valid
- **WHEN** `am/epics/reporting-overhaul/epic.md` starts with
  `# reporting-overhaul`, `Status: draft`, opens with an `## Introduction`
  carrying a `### Non-goals` subsection, carries `## Decisions`, `## Design`,
  and `## Changes`, and its stub table lists `csv-export` with ratings
  `low`/`medium`/`low`/`low`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Missing introduction is rejected
- **WHEN** an epic carries `## Decisions`, `## Design`, and `## Changes` but
  no `## Introduction` section
- **THEN** tooling reports the missing section

#### Scenario: Introduction must come first
- **WHEN** an epic's first level-2 section is `## Decisions` and an
  `## Introduction` appears later in the document
- **THEN** tooling reports that the Introduction is not the opening section

#### Scenario: Missing non-goals is rejected
- **WHEN** an epic's `## Introduction` has no `### Non-goals` subsection
- **THEN** tooling reports the missing subsection

#### Scenario: Invalid rating is rejected
- **WHEN** a stub row's Risk cell reads `huge`
- **THEN** tooling reports the invalid rating

#### Scenario: Epic-level verified does not exist
- **WHEN** an epic's status line reads `Status: verified`
- **THEN** tooling treats the status as invalid
