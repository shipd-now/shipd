## MODIFIED Requirements

### Requirement: Epic structural validation
id: epic-structural-validation
base: e09b7063f324
Dropped: A cycle is not a lint error

The linter SHALL validate every epic under `.shipd/epics/` during library linting
and SHALL provide an `--epic <slug>` mode linting a single epic, enforcing the
epic artifact layout and header metadata rules (title, status vocabulary,
recognized keys, required sections, stub table shape). The stub table check
SHALL accept a header of the six standard columns, or the six followed by
`After`; where `After` is present, it SHALL error on an `After` slug that is
not kebab-case, names no other row of the table, or names the row itself,
and SHALL error on a dependency cycle among the rows, reporting the first
cycle found in table order as one error naming its slugs as `a -> b -> a`.
When linting a change
whose plan carries `Epic:`, the linter SHALL error on an unresolvable epic
reference and SHALL warn — never error — when the resolved epic's stub table
lacks the change's slug. A repository with no `.shipd/epics/` directory SHALL
lint exactly as before this feature.

#### Scenario: Library lint covers epics
- **WHEN** library linting runs in a repo whose `.shipd/epics/broken/epic.md` has
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
- **WHEN** library linting runs in a repo without `.shipd/epics/`
- **THEN** no epic errors or warnings are emitted and the exit code is
  unaffected

#### Scenario: Seven-column table with valid After lints clean
- **WHEN** `--epic waves` runs against an epic whose table header ends in
  `After` and row `b` holds `a` in that cell
- **THEN** the linter prints OK and exits zero

#### Scenario: Self-reference and unknown slug are errors
- **WHEN** row `b`'s `After` cell reads `b, zz`
- **THEN** the linter reports that `b` names itself and that `zz` is not a
  row of the table, and exits non-zero

#### Scenario: A cycle is a lint error
- **WHEN** row `a` is after `b` and row `b` is after `a`
- **THEN** the linter reports an error naming the cycle `a -> b -> a` and
  exits non-zero
