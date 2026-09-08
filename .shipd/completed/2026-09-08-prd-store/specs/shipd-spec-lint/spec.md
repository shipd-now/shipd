## ADDED Requirements

### Requirement: PRD lint mode
id: prd-lint-mode

The linter SHALL provide a `--prd <slug>` mode validating a single PRD's
structure per the PRD store grammar and its declared tier's section contract
at the workspace's resolved PRD path
(`<ws>/<content-dir>/prds/<slug>/prd.md`), resolving the workspace from
`--root`; when no workspace root is discoverable, the mode SHALL exit
non-zero with an error saying no workspace was found. Library and change
linting SHALL NOT walk the workspace's prds directory.

#### Scenario: Valid PRD lints clean
- **GIVEN** a discoverable workspace whose `prds/mobile-push/prd.md`
  conforms to the grammar and its `Template: basic` section contract
- **WHEN** `spec_lint.py --prd mobile-push` runs
- **THEN** it exits `0` and prints an OK line

#### Scenario: Violations are reported with the PRD path
- **WHEN** `--prd` runs against a PRD missing its tier's `## Non-goals`
  section
- **THEN** the finding names the missing section and the PRD's file path,
  and the exit code is non-zero

#### Scenario: No workspace is an error
- **WHEN** `--prd mobile-push` runs from a root with no discoverable
  workspace
- **THEN** the linter exits non-zero with an error saying no workspace was
  found from that root

#### Scenario: Library lint ignores the prds directory
- **WHEN** a malformed PRD exists in the workspace and the repo's library
  lint runs with no mode flag
- **THEN** the library lint result is unaffected by the PRD
