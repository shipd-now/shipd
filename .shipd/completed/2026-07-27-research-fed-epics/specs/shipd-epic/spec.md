## ADDED Requirements

### Requirement: Research-fed epic authoring
id: research-fed-authoring

Where research is supplied for the feature — reports the user names, or
files the epic under authoring already links — the `/s:epic` skill SHALL
read those research files as pre-investigation context before its question
round, and SHALL record every consumed report as a link entry in the
epic's `## Research` section. The skill SHALL NOT invent research entries
for files it did not read, and epics for features with no research SHALL
be authored exactly as before, with no `## Research` section.

#### Scenario: Supplied research is consumed and recorded
- **GIVEN** the user points epic authoring at
  `.shipd/research/payment-apis/report.md`
- **WHEN** the epic is emitted
- **THEN** its `## Research` section links that report and the epic's
  Decisions reflect context drawn from it

#### Scenario: No research means no section
- **WHEN** an epic is authored with no research supplied or discovered
- **THEN** the emitted epic carries no `## Research` section
