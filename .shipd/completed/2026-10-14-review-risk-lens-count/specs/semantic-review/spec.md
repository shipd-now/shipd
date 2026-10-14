## MODIFIED Requirements

### Requirement: Risk lenses
id: review-risk-lenses
base: 0db75923ac49

The `/s:review` skill SHALL carry five risk lenses alongside its existing
judgement passes — security, performance, stability, data integrity, and
packaging — expressed as six triggers: secret or credential exposure,
authorization boundary, unbounded work, resource release, migration
reversibility, and packaging and dependency manifests. The
triggers SHALL be stated inline in `SKILL.md`, read on every review, and SHALL
NOT be gated on a cohort, a file type, or any other condition. The detailed
guidance and worked examples for the lenses SHALL live in
`plugins/s/skills/review/references/risk-lenses.md`, read when a trigger fires.

That reference file SHALL state those same two counts in its own header and
SHALL carry one section per trigger, so a reviewer opening it is never told to
expect a different number from the one it documents. Its header stated "Five
triggers, four lenses" — both figures wrong, and transposed — while
documenting six sections, and it stayed that way through every version of this
skill because nothing compared the header to the sections.

A finding of secret or credential exposure, or of an authorization boundary
reached without the caller's scope check, SHALL carry severity `high`
regardless of the reviewer's confidence. Findings from the remaining triggers
SHALL rate on the existing high, medium and low rubric with no floor.

A packaging finding that a file the diff adds is omitted from what the manifest
publishes SHALL anchor at the manifest — the line a fix would change — and
SHALL name the importing line as a further location under the general
further-location permission the review skill states, because the import is the
line at which the omission surfaces at run time — the import itself is correct,
and that is why it qualifies under the run-time shape rather than by being
wrong on its own terms.

The `--json` finding taxonomy SHALL accept the values `security`,
`performance`, `stability`, and `data-integrity` in addition to those it
already accepts.

Both surfaces that cannot read a reference file — the harness command body at
`plugins/s/harness/bodies/review.md` and the vendored template at
`plugins/s/integrations/copilot/SKILL.md` — SHALL carry the lens guidance and
the exposure severity floor inline.

#### Scenario: Every trigger is inline and ungated
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** all six triggers appear in the workflow itself, and no trigger is
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
- **THEN** each names all six triggers and the exposure severity floor in its
  own body, referencing no file under `skills/review/references/`

#### Scenario: The new reference is pinned like the others
- **WHEN** the review skill's test suite runs
- **THEN** `risk-lenses.md` is named in the References table, its path
  resolves, and its `Load when` cell and its condition sentence share at least
  the required content words

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is within the line ceiling `review-skill-references` owns

#### Scenario: A new file the manifest never publishes is a finding
- **WHEN** the diff adds a module and requires it, while the manifest's
  published-paths allowlist still omits it
- **THEN** the review reports it, since the published artifact lacks the
  module even though the repository's own tests pass

#### Scenario: A dependency only the lockfile declares is a finding
- **WHEN** code requires a package that the lockfile carries transitively but
  the manifest never declares
- **THEN** the review reports it against the manifest's omission

#### Scenario: Lockfile churn alone is not a finding
- **WHEN** a lockfile changes hashes or ordering with no dependency added,
  removed, or re-ranged
- **THEN** the review reports nothing for it

#### Scenario: A file-not-shipped finding names the import too
- **WHEN** the diff adds a module, requires it from an entry point, and the
  manifest's published-files allowlist omits it
- **THEN** the finding's primary location is the manifest and its locations
  also name the importing line

#### Scenario: The reference file's header matches what it documents
- **WHEN** `plugins/s/skills/review/references/risk-lenses.md` is inspected
- **THEN** its header states six triggers and five lenses, and the file carries
  one `##` section per trigger `SKILL.md` names

