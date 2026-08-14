## ADDED Requirements

### Requirement: Epic research section
id: epic-research-section

An epic MAY carry a `## Research` section associating research with the
epic. When present, the section SHALL hold at least one markdown list entry
whose link targets a file under the content directory's `research/` folder
(default `.shipd/research/`); annotation prose MAY follow a link on its line.
When absent, the epic SHALL be exactly as valid as before this feature. The
system SHALL reserve `<content-dir>/research/` as the home of research
artifacts; this requirement mandates no internal format for them.

#### Scenario: Epic lists an existing research report
- **GIVEN** a file at `.shipd/research/payment-apis/report.md`
- **WHEN** an epic carries a `## Research` section with the entry
  `- [Payment APIs](../../research/payment-apis/report.md)`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Research section is optional
- **WHEN** an epic carries no `## Research` section
- **THEN** no research-related finding is reported

#### Scenario: Empty research section is rejected
- **WHEN** an epic carries a `## Research` section with no link entries
- **THEN** tooling reports the empty section as an error
