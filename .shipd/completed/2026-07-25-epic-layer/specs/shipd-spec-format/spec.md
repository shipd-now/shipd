## ADDED Requirements

### Requirement: Epic artifact layout
id: epic-artifact-layout

An epic SHALL live at `am/epics/<slug>/epic.md`, beginning with a `# <slug>`
title matching its directory, a `Status:` line whose value is one of `draft`,
`ready`, `active`, `complete`, and optionally a header metadata block. The
document SHALL carry `## Decisions`, `## Design`, and `## Changes` sections,
and `## Changes` SHALL hold a stub table with the exact columns
`| Change | Description | Code | Integration | Unknowns | Risk |`, at least
one data row, kebab-case change slugs unique within the table, and every
rating cell one of `low`, `medium`, `high`.

#### Scenario: Conforming epic is valid
- **WHEN** `am/epics/reporting-overhaul/epic.md` starts with
  `# reporting-overhaul`, `Status: draft`, carries the three sections, and its
  stub table lists `csv-export` with ratings `low`/`medium`/`low`/`low`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Invalid rating is rejected
- **WHEN** a stub row's Risk cell reads `huge`
- **THEN** tooling reports the invalid rating

#### Scenario: Epic-level verified does not exist
- **WHEN** an epic's status line reads `Status: verified`
- **THEN** tooling treats the status as invalid

### Requirement: Epic header metadata
id: epic-header-metadata

An epic's header metadata block SHALL recognize exactly two keys — `Theme:`
and `Initiative:` — with kebab-case values; `Theme:` SHALL be validated
against `valid_themes` when `am/config.json` declares a non-empty vocabulary,
and any other key (including `Profile:` and `Epic:`) SHALL be rejected.

#### Scenario: Epic carries theme and initiative
- **WHEN** an epic header carries `Theme: reliability` and
  `Initiative: mvp-readiness`
- **THEN** both are parsed as the epic's metadata and accepted

#### Scenario: Profile on an epic is rejected
- **WHEN** an epic header carries `Profile: lite`
- **THEN** tooling reports an unrecognized-key error

### Requirement: Epic reference resolution
id: epic-reference-resolution

A change plan's `Epic: <slug>` line SHALL resolve to an existing
`am/epics/<slug>/epic.md`; an unresolvable reference SHALL be an error. Where
the referenced epic's stub table does not list the change's slug, tooling
SHALL surface a warning — membership drift is visible but not fatal.

#### Scenario: Dangling epic reference is an error
- **WHEN** a change carries `Epic: no-such-epic` and `am/epics/no-such-epic/`
  does not exist
- **THEN** tooling reports an error for the unresolvable reference

#### Scenario: Missing stub row warns
- **GIVEN** `am/epics/reporting-overhaul/epic.md` exists but its stub table
  has no `csv-export` row
- **WHEN** change `csv-export` carrying `Epic: reporting-overhaul` is checked
- **THEN** tooling emits a warning naming the missing membership row and the
  check still passes
