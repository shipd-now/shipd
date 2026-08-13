## MODIFIED Requirements

### Requirement: Plan metadata validation
id: plan-metadata-validation
base: 4a68231facfe

When linting a change, the linter SHALL validate the plan's header metadata
block: it SHALL error on an unrecognized key in the block, on a value that
is not a kebab-case slug, on a `Profile:` value other than `full` or `lite`,
on a plan carrying both `Epic:` and `Initiative:` lines, and on a `Theme:`
value outside `valid_themes` when the resolved layered configuration
declares a non-empty vocabulary. A plan with no metadata block SHALL lint
exactly as it did before this feature.

#### Scenario: Unrecognized key errors
- **WHEN** a plan's metadata block contains `Them: reliability`
- **THEN** the linter reports an error naming the unrecognized key and
  exits non-zero

#### Scenario: Theme outside declared vocabulary errors
- **GIVEN** the repo's `.shipd-config.json` declares
  `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: speed`
- **THEN** the linter reports an error naming the invalid theme

#### Scenario: Epic with initiative errors
- **WHEN** a plan carries both `Epic:` and `Initiative:` lines
- **THEN** the linter reports an error stating the initiative must attach
  to the epic

### Requirement: Initiative lint mode
id: initiative-lint-mode
base: a5fd9f2303b5

The linter SHALL provide an `--initiative <slug>` mode validating a single
brief's structure per the initiative brief artifact rules at the workspace's
resolved brief path (`<ws>/<content-dir>/initiatives/<slug>/brief.md`),
resolving the workspace from `--root`; when no workspace root is
discoverable, the mode SHALL exit non-zero with an error saying no workspace
was found. Library and change linting SHALL NOT walk the workspace's
initiatives directory — briefs enter repo lint only through the CI-safe
`Initiative:` reference resolution.

#### Scenario: Valid brief lints clean
- **GIVEN** a discoverable workspace with a conforming
  `.shipd/initiatives/mvp-readiness/brief.md`
- **WHEN** `--initiative mvp-readiness` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: No workspace fails the mode
- **WHEN** `--initiative mvp-readiness` runs where no workspace root is
  discoverable
- **THEN** the linter exits non-zero saying no workspace was found

### Requirement: Workspace lint mode
id: workspace-lint-mode
base: 50f1d8010e03

The linter SHALL provide a `--workspace` mode that resolves the workspace
from `--root` and reports the registry-validation findings against the
workspace root's `.shipd-config.json` `workspace` object, exiting zero on a
clean registry and non-zero otherwise; when no workspace root is
discoverable, the mode SHALL exit non-zero saying no workspace was found.
Library and change linting SHALL remain registry-silent except where a
brief's `Project:` line requires the registry.

#### Scenario: Clean registry passes
- **GIVEN** a discoverable workspace whose registry validates clean
- **WHEN** `--workspace` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: Registry findings name the config file
- **WHEN** `--workspace` runs against a registry with a duplicate repo path
- **THEN** the error is reported naming `.shipd-config.json` and the exit code
  is non-zero
