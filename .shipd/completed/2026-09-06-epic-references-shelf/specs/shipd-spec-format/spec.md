## ADDED Requirements

### Requirement: Epic References section
id: epic-references-section

An epic MAY carry a `## References` section associating reference documents
of any installed kind with the epic. When the section is present, it SHALL
hold at least one markdown list entry `- [title](path)` whose link resolves —
first relative to the epic's own directory, then relative to the repository
root — to an existing file under the content directory's `research/`,
`video/`, or `docs/` folder, and entries of the three kinds MAY mix freely in
the one section. The section SHALL be additive: the `## Research` and
`## Video` sections keep their existing semantics unchanged, an epic MAY
carry any combination of the three sections, and when `## References` is
absent the epic SHALL be exactly as valid as before.

#### Scenario: Mixed-kind entries resolve
- **WHEN** an epic's `## References` section links
  `../../research/payment-apis/report.md`,
  `../../video/kickoff-call/brief.md`, and
  `../../docs/strategy-notes/doc.md`, each an existing file
- **THEN** the epic passes the section's validation

#### Scenario: References section is optional
- **WHEN** an epic carries no `## References` section
- **THEN** no finding is produced for the section

#### Scenario: Legacy sections are valid alongside References
- **WHEN** an epic carries a `## Research` section, a `## Video` section, and
  a `## References` section, each with resolving entries
- **THEN** all three sections pass validation with their existing semantics
