## ADDED Requirements

### Requirement: Initiative lint mode
id: initiative-lint-mode

The linter SHALL provide an `--initiative <slug>` mode validating a single
brief's structure per the initiative brief artifact rules, resolving the
workspace from `--root`; when no workspace root is discoverable, the mode
SHALL exit non-zero with an error saying no workspace was found. Library and
change linting SHALL NOT walk `initiatives/` — briefs enter repo lint only
through the CI-safe `Initiative:` reference resolution.

#### Scenario: Valid brief lints clean
- **GIVEN** a discoverable workspace with a conforming
  `initiatives/mvp-readiness/brief.md`
- **WHEN** `--initiative mvp-readiness` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: Structural violations are reported
- **WHEN** `--initiative` runs against a brief whose status is `pending` and
  whose `## Requirements` section is missing
- **THEN** the linter reports both errors and exits non-zero

#### Scenario: No workspace fails the mode
- **WHEN** `--initiative mvp-readiness` runs where no workspace root is
  discoverable
- **THEN** the linter exits non-zero saying no workspace was found

#### Scenario: Library lint ignores briefs
- **WHEN** library linting runs in a repo whose workspace contains a
  malformed brief that no epic or change references
- **THEN** the malformed brief produces no library-lint error
