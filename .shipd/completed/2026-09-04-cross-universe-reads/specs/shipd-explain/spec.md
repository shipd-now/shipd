## MODIFIED Requirements

### Requirement: Missing or unknown epic lists the roster and stops
id: explain-missing-epic
base: 4fd726bda635

If `/s:explain` is invoked with no slug, or with a slug the engine cannot
resolve (`cat epic` exits non-zero), then the skill SHALL report the engine's
error (when one was produced), list the available epic slugs through the
engine's roster verb — `shipd list epics`, which spans the invocation root
and its worktrees — and stop without explaining anything. The skill SHALL NOT
list the roster by reading the spec tree's directory names itself.

#### Scenario: Unknown slug reports and lists
- **WHEN** `/s:explain no-such-epic` is invoked
- **THEN** the skill reports the engine's `epic 'no-such-epic' not found`
  error, prints the epic slugs `shipd list epics` reports, and stops

#### Scenario: No argument lists the roster
- **WHEN** `/s:explain` is invoked with no argument
- **THEN** the skill prints the epic slugs `shipd list epics` reports, asks
  the user to pick one, and stops

#### Scenario: A worktree-hosted epic appears in the roster
- **WHEN** `/s:explain` is invoked bare in a repo whose worktree alone hosts
  an epic
- **THEN** the printed roster includes that epic's slug
