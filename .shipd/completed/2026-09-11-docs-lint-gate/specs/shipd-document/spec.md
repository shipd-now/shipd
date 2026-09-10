## ADDED Requirements

### Requirement: Marker-gated docs lint in CI
id: docs-ci-marker-gate

The repository's CI workflow (`.github/workflows/ci.yml`) SHALL carry a step
that selects the markdown files under `docs/` (recursive), excluding
`docs/retros/`, whose first line contains a doc-type marker comment
(`<!-- doc-type:`, with optional spaces after `<!--`), and runs
`plugins/s/skills/document/scripts/docs_lint.py` over the selected files. If a
selected file produces a lint error, then the step SHALL fail with a non-zero
exit. When no file qualifies, the step SHALL print a skip notice and pass
without invoking the lint. The selection SHALL NOT validate the marker's type
value — a first line carrying the marker comment with an unknown or malformed
type is selected, so the lint reports it rather than the filter hiding it.

#### Scenario: Marker doc with an error fails the workflow step
- **WHEN** the step's `run:` body executes against a `docs/` tree holding a
  file whose first line is a doc-type marker and whose content violates the
  standard (e.g. an unknown type or an over-cap file)
- **THEN** the step exits non-zero

#### Scenario: Clean marker doc passes
- **WHEN** the step's `run:` body executes against a `docs/` tree whose only
  marker-carrying file conforms to the standard
- **THEN** the step exits 0

#### Scenario: No marker-carrying docs is a pass
- **WHEN** the step's `run:` body executes against a `docs/` tree where no
  file's first line carries a doc-type marker
- **THEN** the step prints a skip notice and exits 0 without running the lint

#### Scenario: Retros are exempt
- **WHEN** the step's `run:` body executes against a tree whose only
  marker-carrying file sits under `docs/retros/` and would fail the lint
- **THEN** the file is not selected and the step exits 0
