# semantic-review

## ADDED Requirements

### Requirement: Risk lenses
id: review-risk-lenses

The `/s:review` skill SHALL carry four risk lenses alongside its existing
judgement passes — security, performance, stability, and data integrity —
expressed as five triggers: secret or credential exposure, authorization
boundary, unbounded work, resource release, and migration reversibility. The
triggers SHALL be stated inline in `SKILL.md`, read on every review, and SHALL
NOT be gated on a cohort, a file type, or any other condition. The detailed
guidance and worked examples for the lenses SHALL live in
`plugins/s/skills/review/references/risk-lenses.md`, read when a trigger fires.

A finding of secret or credential exposure, or of an authorization boundary
reached without the caller's scope check, SHALL carry severity `high`
regardless of the reviewer's confidence. Findings from the remaining triggers
SHALL rate on the existing high, medium and low rubric with no floor.

The `--json` finding taxonomy SHALL accept the values `security`,
`performance`, `stability`, and `data-integrity` in addition to those it
already accepts.

Both surfaces that cannot read a reference file — the harness command body at
`plugins/s/harness/bodies/review.md` and the vendored template at
`plugins/s/integrations/copilot/SKILL.md` — SHALL carry the lens guidance and
the exposure severity floor inline. `SKILL.md` SHALL stay under 300 lines.

#### Scenario: Every trigger is inline and ungated
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** all five triggers appear in the workflow itself, and no trigger is
  stated only in the References table or only in a reference file

#### Scenario: A leaked credential is high
- **WHEN** a review finds a new literal, log line, or error message carrying a
  key, token, or personal data
- **THEN** the finding's severity is `high` and the verdict is Fix required

#### Scenario: An unguarded authorization boundary is high
- **WHEN** a review finds a new route, handler, or query reaching data without
  the caller's scope check
- **THEN** the finding's severity is `high`

#### Scenario: The remaining lenses carry no floor
- **WHEN** a review finds an unbounded loop whose cost the reviewer judges
  minor
- **THEN** the finding may rate `low` or `medium`, since only the two exposure
  triggers carry a floor

#### Scenario: The taxonomy accepts the lens values
- **WHEN** a `--json` review emits a finding from the data-integrity trigger
- **THEN** `data-integrity` is a value the finding shape accepts

#### Scenario: The reference-free surfaces carry the lenses inline
- **WHEN** `plugins/s/harness/bodies/review.md` and
  `plugins/s/integrations/copilot/SKILL.md` are inspected
- **THEN** each names all five triggers and the exposure severity floor in its
  own body, referencing no file under `skills/review/references/`

#### Scenario: The new reference is pinned like the others
- **WHEN** the review skill's test suite runs
- **THEN** `risk-lenses.md` is named in the References table, its path
  resolves, and its `Load when` cell and its condition sentence share at least
  the required content words

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines
