## MODIFIED Requirements

### Requirement: Status CLI
id: status-cli
base: 56a4934d1df3

A stdlib-Python CLI SHALL provide: `show [change]` printing the change's
status and task progress; `status [change]` printing the bare status value
(`?` when missing or invalid); `validate [change]` checking the change's
structural validity and exiting non-zero with the errors when invalid;
`set-status <status> [change]` writing a validated status value into the
`plan.md` header (inserting the header if absent) subject to the
transition guards; and `sync [change]` re-deriving the status from
`tasks.md` — mapping all-done to `complete`, any-done-or-in-progress to
`active`, and none-started to `ready` — while never changing a status of
`draft`, `verified`, or `rejected`. No unguarded setter SHALL exist. Where
`[change]` is omitted, the CLI SHALL default to the currently selected
spec and SHALL exit non-zero with an error when none is selected — except
`show`, which SHALL instead print the workspace board report (see the
Workspace board report requirement) when no name is given and no spec is
selected; `status` SHALL keep the error in that case. When the
given name matches no change but an epic of that slug exists — discovered
by probing the invocation root first, then each `.worktrees/<name>`
directory under it in sorted name order, resolving each candidate's
content directory independently and skipping unreadable candidates —
`status` SHALL print the epic's status value and `show` SHALL print the
epic's board-shaped report — identical to `epic-show`'s output; a name
matching neither a change nor an epic in any candidate SHALL keep
printing `?` from `status`.

#### Scenario: Sync derives active
- **GIVEN** a change with status `ready`
- **WHEN** `sync` runs after one task is marked done
- **THEN** the plan's status line becomes `active`

#### Scenario: Sync never touches draft, verified, or rejected
- **WHEN** `sync` runs on a change whose status is `draft`, `verified`,
  or `rejected`
- **THEN** the status line is left unchanged

#### Scenario: Set-status validates the value
- **WHEN** `set-status` is invoked with a value outside the six statuses
- **THEN** the CLI writes nothing and exits non-zero with an error

#### Scenario: Status falls back to an epic
- **GIVEN** an epic slug with no change of the same name
- **WHEN** `status <slug>` runs
- **THEN** the epic's status value is printed and the exit code is 0

#### Scenario: Show falls back to the epic report
- **GIVEN** an epic slug with no change of the same name
- **WHEN** `show <slug>` runs
- **THEN** the output is the same board-shaped report `epic-show <slug>`
  prints

#### Scenario: Status falls back to a worktree-hosted epic
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** `status <slug>` runs from the invocation root
- **THEN** that epic's status value is printed and the exit code is 0

#### Scenario: A name that is neither change nor epic stays a question mark
- **WHEN** `status <name>` runs for a name matching no change and no epic
  in the invocation root or any worktree
- **THEN** `?` is printed

#### Scenario: Bare status without a selection still errors
- **GIVEN** no spec selected
- **WHEN** `status` runs with no argument
- **THEN** the CLI exits non-zero with the no-selection error

### Requirement: Epic status verbs
id: epic-status-verbs
base: 08224ce5b6c4

The status CLI SHALL provide `epic-show <slug>` printing the epic's
board-shaped report; `epic-sync <slug>` re-deriving the epic's status from
member states; and `epic-set-status <status> <slug>` writing a validated
epic status (`draft`, `ready`, `active`, `complete`), refusing `ready`
unless the epic lints clean, with refusals printing a `Refused: ` reason
and exiting 3. `epic-show` SHALL resolve the epic by probing the
invocation root first, then each `.worktrees/<name>` directory under it in
sorted name order — resolving each candidate's content directory
independently and skipping unreadable candidates, the invocation root
winning a slug hosted in both — and SHALL read the epic's file and status
from the hosting root; the mutating verbs (`epic-sync`,
`epic-set-status`) SHALL keep resolving the invocation root only. The
board-shaped report SHALL print, in order: the
`<slug>: <status>` line and the epic's header metadata lines (unchanged
from before this report existed); when the epic resolved from a worktree,
a `worktree: <name>` line directly after the metadata lines; a
`shipped <n>/<m>` line where `n` is
the count of members whose derived state is `archived` and `m` the count
of all stub members; a blank line; then the four board lanes in board
order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each printed as a
`<LANE> (<count>)` header even when its count is 0, followed by one
indented line per member in that lane carrying the member's slug, its
derived state, its stub-table risk rating as `risk <value>` (`?` when the
row carries none), and a `[worktree]` marker when its state was derived
from a worktree rather than the invocation root. A member's lane SHALL be
derived from its state alone — `archived`→`shipped`, `ready`→`ready`,
`unplanned`→`unplanned`, every other state→`building`, rendered as the
uppercase lane headers — and that projection SHALL be a single shared
function the dashboard's flow-lane mapping also consumes, so the report
and the board cannot drift. A
member's state SHALL be derived by probing candidate roots in order — the
invocation root first, then each `.worktrees/<name>` directory under it in
sorted name order — resolving each candidate's content directory
independently and skipping any candidate whose configuration is unreadable.
For each candidate in turn, the state SHALL be `archived` when a matching
`completed/*-<slug>/` exists there, else that candidate's plan status when
`planned/<slug>/` exists there; the first candidate that yields a state wins.
When no candidate yields one, the state SHALL be `unplanned`.
`epic-sync` SHALL derive: all members archived →
`complete`; any member archived or with plan status `active`, `complete`, or
`verified` → `active`; otherwise `ready` — and SHALL never change an epic
whose status is `draft`.

#### Scenario: Members are grouped into board lanes
- **GIVEN** an epic whose stub table lists one member with a matching
  `completed/*-<slug>/` and one member planned nowhere
- **WHEN** `epic-show` runs
- **THEN** the archived member is listed under `SHIPPED (1)` and the other
  under `UNPLANNED (1)`

#### Scenario: Empty lanes still print their header
- **GIVEN** an epic none of whose members is `ready`
- **WHEN** `epic-show` runs
- **THEN** the report contains a `READY (0)` header with no member lines
  under it

#### Scenario: The shipped progress line counts archived members
- **GIVEN** an epic with two archived members among seven
- **WHEN** `epic-show` runs
- **THEN** the report contains `shipped 2/7`

#### Scenario: A worktree-hosted member is marked
- **GIVEN** a member whose state derives from `.worktrees/<member>/` rather
  than the invocation root
- **WHEN** `epic-show` runs
- **THEN** that member's line carries `[worktree]`

#### Scenario: A member planned in its own worktree is not unplanned
- **GIVEN** a repository whose epic lists a member with no change under the
  invocation root's `planned/`, but with a `ready` change under
  `.worktrees/<member>/`'s planned directory
- **WHEN** `epic-show` runs from the invocation root
- **THEN** that member's derived state is `ready`, not `unplanned`

#### Scenario: The invocation root wins over a worktree
- **GIVEN** a member with a change under the invocation root's `planned/` and a
  different plan status for the same slug under a worktree
- **WHEN** the member's state is derived
- **THEN** the invocation root's status is the one reported

#### Scenario: An unreadable worktree config does not break derivation
- **GIVEN** a worktree whose content-directory configuration cannot be read
- **WHEN** a member's state is derived from the invocation root
- **THEN** that worktree is skipped and derivation completes without raising

#### Scenario: Epic-show resolves a worktree-hosted epic
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** `epic-show <slug>` runs from the invocation root
- **THEN** the report prints with the epic's status on the first line and a
  `worktree: <name>` line after the metadata lines

#### Scenario: Mutating verbs stay invocation-root-only
- **GIVEN** an epic hosted only under a worktree
- **WHEN** `epic-set-status ready <slug>` runs from the invocation root
- **THEN** the CLI exits non-zero with the epic-not-found error and writes
  nothing

#### Scenario: Sync derives active from one started member
- **GIVEN** a `ready` epic whose stub table lists two members, one of which
  is an `active` change under `am/planned/`
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `active`

#### Scenario: Sync derives complete when all members are archived
- **GIVEN** an epic whose every stub slug matches an `am/completed/*-<slug>/`
  directory
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `complete`

#### Scenario: Sync never touches a draft epic
- **WHEN** `epic-sync` runs on an epic whose status is `draft`
- **THEN** the status line is left unchanged

### Requirement: Workspace board report
id: workspace-board-report
base: 8958a7fa7b53

When `show` runs with no name given and no spec selected, the status CLI
SHALL print a workspace board report derived from the spec tree alone, in
order: a `N specs · N epics · N initiatives` totals line — members summed
across every epic, the epic count, and the distinct `Initiative:` slugs
across epic files, matching the board header's totals; a `shipped <n>/<m>`
line over every rendered row (epic members plus standalone changes), `n`
counting those whose lane is `shipped`; a blank line; then the four board
lanes in board order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each
printed as a `<LANE> (<count>)` header even when its count is 0. The
report's epics SHALL be discovered by probing the invocation root first,
then each `.worktrees/<name>` directory under it in sorted name order —
resolving each candidate's content directory independently, skipping
unreadable candidates, the invocation root winning a slug hosted in
both — each epic read from its hosting root, so the totals and rows match
the board's worktree-aware aggregation. In the
non-shipped lanes each member SHALL print as one indented row carrying its
epic's slug (or `standalone` for a change planned outside any epic), the
member slug, its derived state, `risk <value>` (`?` when absent), and a
`[worktree]` marker when its state was derived from a worktree. The
`SHIPPED` lane SHALL print per-epic rollup rows — `<epic-slug> (<n>)` for
each epic with shipped members, plus `standalone (<n>)` last when any
standalone change is archived — never flat member rows. Lanes SHALL derive
from the shared state→lane projection, and standalone changes SHALL be
discovered by the same single implementation the dashboard's board
aggregation consumes. An unreadable epic file SHALL be skipped, never
raised.

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
