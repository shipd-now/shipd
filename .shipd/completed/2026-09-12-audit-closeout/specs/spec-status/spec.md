## MODIFIED Requirements

### Requirement: Workspace board report
id: workspace-board-report
base: c1ccc658244a

When `show` runs with no name given and no spec selected, the status CLI
SHALL print a workspace board report derived from the spec tree alone, in
order: a `N specs · N epics · N initiatives` totals line — members summed
across every epic, the epic count, and the distinct `Initiative:` slugs
across epic files, matching the board header's totals; a `shipped <n>/<m>`
line over every rendered row (epic members plus standalone changes), `n`
counting those whose lane is `shipped`; a blank line; then the four board
lanes in board order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each
printed as a `<LANE> (<count>)` header even when its count is 0.

The report SHALL obtain its universes through the engine's shared
universe-discovery seam (shipd-workspace workspace-universe-discovery),
never a private reimplementation: the invocation root's own universe always
— its epics discovered by probing the invocation root first, then each
`.worktrees/<name>` directory under it in sorted name order, resolving each
candidate's content directory independently, skipping unreadable
candidates, the invocation root winning a slug hosted in both — plus, for a
workspace-level invocation, one universe per declared project repo the seam
yields, each aggregated exactly as an invocation root is (its own epics,
worktrees, member-state derivation, and standalone-change discovery, all
relative to that repo). When the seam yields no project universes, the
report SHALL cover only the invocation root's universe and its output SHALL
be byte-identical to the single-universe rendering. Epic slugs SHALL NOT be
deduplicated across universes; totals sum across every universe and
`initiatives` counts distinct slugs across universes.

In the non-shipped lanes each member SHALL print as one indented row
carrying its epic's slug (or `standalone` for a change planned outside any
epic), the member slug, its derived state, `risk <value>` (`?` when absent),
a `[worktree]` marker when its state was derived from a worktree of its
owning universe, and — for a row from a project universe — a `[<project>]`
marker after the worktree marker position. The `SHIPPED` lane SHALL print
rollup rows counted per epic per owning project — `<epic-slug> (<n>)` for
invocation-root rows, `<epic-slug> [<project>] (<n>)` for project rows, plus
`standalone` rollups last within each universe's grouping — never flat
member rows. Rows SHALL collect epics first (the invocation root's, then
each project universe's in slug order), then standalone changes in the same
universe order. Lanes SHALL derive from the shared state→lane projection,
and standalone changes SHALL be discovered by the same single implementation
the dashboard's board aggregation consumes, per universe with that
universe's own member-slug exclusion set. An unreadable epic file SHALL be
skipped, never raised.

#### Scenario: Bare show reports the workspace
- **GIVEN** a repository with epics and no spec selected
- **WHEN** `show` runs with no argument
- **THEN** the totals line, the `shipped <n>/<m>` line, and all four lane
  headers with counts are printed, and the exit code is 0

#### Scenario: Non-shipped rows carry their epic context
- **GIVEN** an epic `e1` with an unplanned member `m1`
- **WHEN** the workspace report prints
- **THEN** `m1`'s row sits under `UNPLANNED` and carries `e1`, `m1`, the
  state `unplanned`, and its risk

#### Scenario: Shipped lane rolls up per epic
- **GIVEN** two epics each with archived members
- **WHEN** the workspace report prints
- **THEN** the `SHIPPED` lane holds one `<epic-slug> (<n>)` row per epic
  and no flat member rows

#### Scenario: A standalone change folds in
- **GIVEN** a change planned under `planned/` whose plan carries no `Epic:`
  header and whose slug appears in no epic
- **WHEN** the workspace report prints
- **THEN** it appears as a row under its lane with the epic column
  `standalone`

#### Scenario: A worktree-authored epic counts in the report
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** the workspace report prints from the invocation root
- **THEN** the epic count includes it, its members are summed into the
  totals, and its member rows render under their lanes

#### Scenario: Declared project epics aggregate at workspace level
- **GIVEN** a workspace root whose registry declares a project whose repo
  directory holds an epic with members
- **WHEN** `show` runs bare from the workspace root
- **THEN** the epic counts in the totals, its member rows render under
  their lanes with the project's `[<slug>]` marker, and their states derive
  from the project repo

#### Scenario: Inside a member repo the board stays per-repo
- **GIVEN** the same workspace, invoked from inside a declared project repo
- **WHEN** `show` runs bare there
- **THEN** only that repo's universe is reported — no other project's epics
  appear and no `[<slug>]` markers print

#### Scenario: A project's standalone change folds in
- **GIVEN** a declared project repo holding a change planned outside any
  epic
- **WHEN** the workspace report prints from the workspace root
- **THEN** the change appears under its lane with the epic column
  `standalone` and the project's marker

#### Scenario: An absent project repo is skipped
- **GIVEN** a registry declaring a repo path that is not a directory on
  this machine
- **WHEN** the workspace report prints from the workspace root
- **THEN** the report renders without error and without that repo's
  universe

#### Scenario: Same epic slug in two projects stays distinct
- **GIVEN** two declared project repos each hosting an epic with the same
  slug
- **WHEN** the workspace report prints from the workspace root
- **THEN** both epics count and their rows are distinguished by their
  project markers

#### Scenario: A selection still wins
- **GIVEN** a repository with a change currently selected
- **WHEN** the bare show verb runs with no change named
- **THEN** it reports that change rather than the workspace board
