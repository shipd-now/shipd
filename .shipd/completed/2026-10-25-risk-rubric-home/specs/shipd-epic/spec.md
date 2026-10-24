## ADDED Requirements

### Requirement: Stub ratings follow the risk rubric
id: epic-risk-rubric-ratings

When `/s:epic` writes the `## Changes` stub table, it SHALL load
`skills/epic/references/risk-rubric.md` and SHALL rate each member's Code,
Integration, Unknowns, and Risk cells by that rubric's axis descriptors,
each one of `low`, `medium`, or `high`. The stub table SHALL keep its six
columns plus `After` and SHALL NOT gain a Novelty or Overall column.

#### Scenario: Epic cites the rubric for its ratings
- **WHEN** the epic skill and its harness body are read
- **THEN** both cite `skills/epic/references/risk-rubric.md` where they
  describe the four rating cells

#### Scenario: The table shape is unchanged
- **WHEN** `/s:epic` authors an epic after this change
- **THEN** the stub table header is
  `| Change | Description | Code | Integration | Unknowns | Risk | After |`
