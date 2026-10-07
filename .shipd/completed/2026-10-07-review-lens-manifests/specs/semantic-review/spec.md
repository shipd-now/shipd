## MODIFIED Requirements

### Requirement: Risk lenses
id: review-risk-lenses
base: c7d2b43a7f0b

The `/s:review` skill SHALL carry five risk lenses alongside its existing
judgement passes — security, performance, stability, data integrity, and
packaging — expressed as six triggers: secret or credential exposure,
authorization boundary, unbounded work, resource release, migration
reversibility, and packaging and dependency manifests. The
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

### Requirement: Cohort grouping subcommand
id: cohort-grouping
base: 520c4ddf7fa9

The system SHALL provide `semdiff files <base> [<head>]` grouping changed
paths into architectural cohorts using segment-aware rules (contracts,
database, api, frontend, tests; plus shipd-aware groups for content-dir
spec artifacts and plugin skills), falling back to the path's top-level
directory, and emitting JSON with the cohort map and file/cohort counts. A
packaging or dependency manifest — `package.json` and its lockfiles,
`go.mod`/`go.sum`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`,
`Gemfile`, `composer.json`, `pom.xml`, `build.gradle` and their lock
equivalents — SHALL group into `contracts`, matched on its basename so it
lands there wherever in the tree it sits, since it declares what the package
ships, exports and depends on.

#### Scenario: Segment-aware grouping
- **WHEN** `semdiff files main` runs over changes touching
  `plugins/s/skills/review/SKILL.md` and `.shipd/planned/x/plan.md`
- **THEN** the two paths land in the skills and specs cohorts, not in a
  generic top-level bucket

#### Scenario: A manifest groups as a contract wherever it sits
- **WHEN** `semdiff files main` runs over changes touching `package.json`,
  `server/package.json`, `go.mod` and `tests/fixtures/package.json`
- **THEN** all four land in the contracts cohort, the fixture one included
