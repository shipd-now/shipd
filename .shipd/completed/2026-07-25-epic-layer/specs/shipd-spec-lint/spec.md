## ADDED Requirements

### Requirement: Epic structural validation
id: epic-structural-validation

The linter SHALL validate every epic under `am/epics/` during library linting
and SHALL provide an `--epic <slug>` mode linting a single epic, enforcing the
epic artifact layout and header metadata rules (title, status vocabulary,
recognized keys, required sections, stub table shape). When linting a change
whose plan carries `Epic:`, the linter SHALL error on an unresolvable epic
reference and SHALL warn — never error — when the resolved epic's stub table
lacks the change's slug. A repository with no `am/epics/` directory SHALL
lint exactly as before this feature.

#### Scenario: Library lint covers epics
- **WHEN** library linting runs in a repo whose `am/epics/broken/epic.md` has
  no `## Changes` section
- **THEN** the linter reports the epic's error and exits non-zero

#### Scenario: Single-epic mode
- **WHEN** `--epic reporting-overhaul` runs against a conforming epic
- **THEN** the linter prints OK and exits zero

#### Scenario: Change lint resolves the epic reference
- **WHEN** a linted change carries `Epic: no-such-epic`
- **THEN** the linter reports an unresolvable-reference error and exits
  non-zero

#### Scenario: No epics directory changes nothing
- **WHEN** library linting runs in a repo without `am/epics/`
- **THEN** no epic errors or warnings are emitted and the exit code is
  unaffected
