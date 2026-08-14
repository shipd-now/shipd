## ADDED Requirements

### Requirement: Workspace lint mode
id: workspace-lint-mode

The linter SHALL provide a `--workspace` mode that resolves the workspace
from `--root` and reports the registry-validation findings against
`.shipd/workspace.json`, exiting zero on a clean registry and non-zero
otherwise; when no workspace root is discoverable, the mode SHALL exit
non-zero saying no workspace was found. Library and change linting SHALL
remain registry-silent except where a brief's `Project:` line requires the
registry.

#### Scenario: Clean registry passes
- **GIVEN** a discoverable workspace whose registry validates clean
- **WHEN** `--workspace` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: Registry findings are reported
- **WHEN** `--workspace` runs against a registry with a duplicate repo path
  and a non-list `repos` value
- **THEN** both errors are reported naming `.shipd/workspace.json` and
  the exit code is non-zero

#### Scenario: No workspace fails the mode
- **WHEN** `--workspace` runs where no workspace root is discoverable
- **THEN** the linter exits non-zero saying no workspace was found
