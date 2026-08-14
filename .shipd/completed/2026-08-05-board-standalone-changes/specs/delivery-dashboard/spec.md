## ADDED Requirements

### Requirement: Standalone changes on the board
id: board-standalone-changes

The board aggregation SHALL discover **standalone changes** — change
directories under the invocation root's `planned/` and under each
`.worktrees/<name>/`'s `planned/` whose plan header carries no `Epic:` line
and whose slug appears in no epic's stub table — recording each with its
worktree-aware state and hosting location, exposed as a top-level
`standalone` list on the board (empty when none), via a dependency-free
helper (no `textual`). Every lane SHALL render its standalone changes as
normal cards under a `standalone` group (in epic and initiative grouping
modes; flat in `none` mode) placed by the same state→lane mapping epic
members use; the `standalone` group header SHALL carry the per-lane count
but **no run and no open control**. Standalone cards SHALL open the standard
spec-detail modal, resolving artifacts from the change's hosting location.
Standalone content SHALL fold into the diff-aware lane signatures, so a
standalone change appearing, moving, or leaving repaints the affected lanes.
If a discovered directory is unreadable or malformed, then discovery SHALL
skip it rather than fail the board.

#### Scenario: A worktree-planned standalone change appears in its lane
- **GIVEN** a worktree `planned/` change with `Status: active` and no
  `Epic:` line, absent from every epic stub table
- **WHEN** the board renders in epic mode
- **THEN** the building lane shows the change as a card under a
  `standalone` group header carrying the count

#### Scenario: Epic members are not double-listed
- **GIVEN** a change whose slug appears in an epic's stub table and is
  planned in its worktree
- **WHEN** the board aggregates
- **THEN** the change appears only as that epic's member, not in the
  standalone list

#### Scenario: An Epic-tagged plan is not standalone
- **GIVEN** a worktree `planned/` change whose plan header carries an
  `Epic:` line
- **WHEN** the board aggregates
- **THEN** the standalone list does not include it

#### Scenario: The standalone group has no epic controls
- **WHEN** a `standalone` group header renders in any lane
- **THEN** it carries neither a run control nor an open control

#### Scenario: A standalone card opens the spec-detail modal
- **GIVEN** a rendered standalone card whose change lives in a worktree
- **WHEN** the card is selected
- **THEN** the spec-detail modal opens and resolves the change's artifacts
  from that worktree location

#### Scenario: Discovery is dependency-free and fault-tolerant
- **GIVEN** an environment without `textual` and a worktree holding a
  malformed plan file
- **WHEN** the discovery helper runs
- **THEN** it returns the readable standalone changes, skips the malformed
  one, and imports no `textual`

#### Scenario: A standalone change leaving repaints the lane
- **GIVEN** a rendered board showing a standalone change
- **WHEN** the change's worktree directory is removed and the board
  refreshes
- **THEN** the lane's signature differs and the card disappears
