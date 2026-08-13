## ADDED Requirements

### Requirement: Pipeline-show verb
id: pipeline-show-verb

The status CLI SHALL provide `pipeline-show` printing the effective
autonomous pipeline: one line per resolved entry stating its form (stage,
skipped, tool-bound, replaced, or custom) and any bindings with their
fallbacks, plus the provenance of the `autonomous-pipeline` key — the
supplying config file path, or `[default]` when no layer declares it. On a
pipeline that fails validation the verb SHALL print every validation error
and exit non-zero. The verb SHALL NOT require a discoverable workspace or
a selected change, and a defaults-only resolution SHALL exit zero.

#### Scenario: Default pipeline prints with default provenance
- **WHEN** `pipeline-show` runs where no layer declares the key
- **THEN** all six registry stages print in canonical order marked
  `[default]` and the exit code is zero

#### Scenario: Declared pipeline prints entries and provenance
- **GIVEN** a repo config declaring a pipeline with a skipped gate and a
  replaced review carrying `"fallback": "builtin"`
- **WHEN** `pipeline-show` runs
- **THEN** the output shows the gate as skipped, the review as replaced
  with its fallback, and names the repo's config file

#### Scenario: Invalid pipeline errors with findings
- **WHEN** `pipeline-show` runs against a declared entry with an unknown
  stage name
- **THEN** the validation error is printed naming the entry and the exit
  code is non-zero
