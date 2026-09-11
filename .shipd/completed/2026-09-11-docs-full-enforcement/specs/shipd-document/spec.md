## MODIFIED Requirements

### Requirement: Full-scope docs lint in CI
id: docs-ci-marker-gate
base: aa4579b9f9c5

The repository's CI workflow (`.github/workflows/ci.yml`) SHALL carry a step
that selects every markdown file under `docs/` (recursive), excluding
`docs/retros/`, and runs
`plugins/s/skills/document/scripts/docs_lint.py` over the selected files —
with no marker-based filtering, so a file without a first-line doc-type
marker is selected and fails through the lint's own missing-marker error. If
a selected file produces a lint error, then the step SHALL fail with a
non-zero exit. When no file qualifies, the step SHALL print a skip notice
and pass without invoking the lint.

#### Scenario: Unmarked doc fails the workflow step
- **WHEN** the step's `run:` body executes against a `docs/` tree holding a
  markdown file with no first-line doc-type marker
- **THEN** the step exits non-zero and the output names the missing marker

#### Scenario: Marker doc with an error fails the workflow step
- **WHEN** the step's `run:` body executes against a `docs/` tree holding a
  file whose first line is a doc-type marker and whose content violates the
  standard (e.g. an unknown type or an over-cap file)
- **THEN** the step exits non-zero

#### Scenario: Clean tree passes
- **WHEN** the step's `run:` body executes against a `docs/` tree whose every
  non-retro file conforms to the standard, marker included
- **THEN** the step exits 0

#### Scenario: Retros are exempt
- **WHEN** the step's `run:` body executes against a tree whose only markdown
  file sits under `docs/retros/` and would fail the lint
- **THEN** the file is not selected and the step exits 0

#### Scenario: Empty docs tree is a pass
- **WHEN** the step's `run:` body executes against a tree whose `docs/`
  directory holds no markdown file outside `docs/retros/`
- **THEN** the step prints a skip notice and exits 0 without running the lint
