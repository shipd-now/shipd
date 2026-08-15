## ADDED Requirements

### Requirement: Epic video section
id: epic-video-section

An epic MAY carry a `## Video` section associating video intent briefs with the
epic. When present, the section SHALL hold at least one markdown list entry
whose link targets a file under the content directory's `video/` folder
(default `.shipd/video/`); annotation prose MAY follow a link on its line. When
absent, the epic SHALL be exactly as valid as before this feature. The section
SHALL be independent of `## Research`: a brief SHALL NOT be linked from
`## Research`, a research report SHALL NOT be linked from `## Video`, and the
presence of either section SHALL neither imply nor constrain the other.

#### Scenario: Epic lists an existing intent brief
- **GIVEN** a file at `.shipd/video/kickoff-call/brief.md`
- **WHEN** an epic carries a `## Video` section with the entry
  `- [Kickoff call](../../video/kickoff-call/brief.md)`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Video section is optional
- **WHEN** an epic carries no `## Video` section
- **THEN** no video-related finding is reported

#### Scenario: Empty video section is rejected
- **WHEN** an epic carries a `## Video` section with no link entries
- **THEN** tooling reports the empty section as an error

#### Scenario: The two context sections are independent
- **WHEN** an epic carries both a `## Research` section and a `## Video`
  section
- **THEN** each is validated against its own reserved folder and neither
  section's contents affect the other's findings
