## ADDED Requirements

### Requirement: Questions-and-answers section validation
id: qa-section-validation

When a change's `plan.md` carries a `## Questions and answers` section, the
linter SHALL report an error naming the offending entry for: a section holding
no entries, an entry header not matching `### Q<n>: <summary>`, entry numbers
not sequential starting at `Q1`, and an entry missing a `**Question:**`,
`**Answered by:**`, or `**Answer:**` field. When the section is absent, the
linter SHALL report no finding for it.

#### Scenario: Absent section lints clean
- **WHEN** a plan carries no `## Questions and answers` section
- **THEN** the lint reports no questions-and-answers finding

#### Scenario: Malformed entry is an error
- **WHEN** a plan's `## Questions and answers` section holds an entry headed
  `### Q2:` with no `Q1` entry before it, or an entry lacking an
  `**Answer:**` field
- **THEN** the lint exits non-zero with an error naming the offending entry

#### Scenario: Conforming section passes
- **WHEN** a plan's section holds `### Q1:` and `### Q2:` entries each
  carrying `**Question:**`, `**Answered by:**`, and `**Answer:**` fields
- **THEN** the lint reports no questions-and-answers finding
