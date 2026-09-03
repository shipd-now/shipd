## MODIFIED Requirements

### Requirement: Workspace board report
id: workspace-board-report
base: 07418827488c

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

### Requirement: Epic status verbs
id: epic-status-verbs
base: 85b9c2bad082

The status CLI SHALL provide `epic-show <slug>` printing the epic's
board-shaped report; `epic-sync <slug>` re-deriving the epic's status from
member states; and `epic-set-status <status> <slug>` writing a validated
epic status (`draft`, `ready`, `active`, `complete`), refusing `ready`
unless the epic lints clean, with refusals printing a `Refused: ` reason
and exiting 3. `epic-show` SHALL resolve the epic across the universes the
engine's shared universe-discovery seam yields (shipd-workspace
workspace-universe-discovery), in seam order — the invocation root's own
universe first, then each declared project universe in slug order — probing
each universe's root first, then each of its `.worktrees/<name>` directories
in sorted name order, resolving each candidate's content directory
independently and skipping unreadable candidates; the first hosting
universe SHALL win, and the epic's file and status SHALL be read from the
hosting root. The mutating verbs (`epic-sync`, `epic-set-status`) SHALL
keep resolving the invocation root only. The board-shaped report SHALL
print, in order: the `<slug>: <status>` line and the epic's header metadata
lines (unchanged from before this report existed); when the epic resolved
from a worktree of its owning universe, a `worktree: <name>` line directly
after the metadata lines; when the epic resolved from a declared project
universe, a `project: <slug>` line directly after (after any `worktree:`
line); a `shipped <n>/<m>` line where `n` is the count of members whose
derived state is `archived` and `m` the count of all stub members; a blank
line; then the four board lanes in board order — `UNPLANNED`, `READY`,
`BUILDING`, `SHIPPED` — each printed as a `<LANE> (<count>)` header even
when its count is 0, followed by one indented line per member in that lane
carrying the member's slug, its derived state, its stub-table risk rating
as `risk <value>` (`?` when the row carries none), and a `[worktree]`
marker when its state was derived from a worktree rather than the owning
universe's root. A member's lane SHALL be derived from its state alone —
`archived`→`shipped`, `ready`→`ready`, `unplanned`→`unplanned`, every other
state→`building`, rendered as the uppercase lane headers — and that
projection SHALL be a single shared function the dashboard's flow-lane
mapping also consumes, so the report and the board cannot drift. A member's
state SHALL be derived by probing the epic's owning universe's candidate
roots in order — that universe's root first, then each of its
`.worktrees/<name>` directories in sorted name order — resolving each
candidate's content directory independently and skipping any candidate
whose configuration is unreadable. For each candidate in turn, the state
SHALL be `archived` when a matching `completed/*-<slug>/` exists there,
else that candidate's plan status when `planned/<slug>/` exists there; the
first candidate that yields a state wins. When no candidate yields one, the
state SHALL be `unplanned`. `epic-sync` SHALL derive: all members
archived → `complete`; any member archived or with plan status `active`,
`complete`, or `verified` → `active`; otherwise `ready` — and SHALL never
change an epic whose status is `draft`.

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

#### Scenario: Epic-show resolves a project-hosted epic at workspace level
- **GIVEN** a workspace root whose declared project repo hosts the epic
- **WHEN** `epic-show <slug>` runs from the workspace root
- **THEN** the report prints with a `project: <slug>` line after the
  metadata lines and its member states derived from that project repo

#### Scenario: The invocation root's universe wins over a project's
- **GIVEN** the same epic slug hosted under the invocation root and under a
  declared project repo
- **WHEN** `epic-show <slug>` runs from the workspace root
- **THEN** the invocation root's epic is the one reported, with no
  `project:` line

#### Scenario: Mutating verbs stay invocation-root-only
- **GIVEN** an epic hosted only under a worktree
- **WHEN** `epic-set-status ready <slug>` runs from the invocation root
- **THEN** the CLI exits non-zero with the epic-not-found error and writes
  nothing

#### Scenario: Mutating verbs never reach a project universe
- **GIVEN** an epic hosted only under a declared project repo
- **WHEN** `epic-sync <slug>` runs from the workspace root
- **THEN** the CLI exits non-zero with the epic-not-found error and writes
  nothing

#### Scenario: Sync derives active from one started member
- **GIVEN** a `ready` epic whose stub table lists two members, one of which
  is an `active` change under `.shipd/planned/`
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `active`

#### Scenario: Sync derives complete when all members are archived
- **GIVEN** an epic whose every stub slug matches an `.shipd/completed/*-<slug>/`
  directory
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `complete`

#### Scenario: Sync never touches a draft epic
- **WHEN** `epic-sync` runs on an epic whose status is `draft`
- **THEN** the status line is left unchanged

### Requirement: Locate verb
id: locate-verb
base: 90af269c7b22

The status CLI SHALL provide `locate [change]` searching for an installed
change across the universes the engine's shared universe-discovery seam
yields (shipd-workspace workspace-universe-discovery), in seam order — the
invocation root's own universe first, then each declared project universe
in slug order — probing, within each universe, that universe's resolved
`planned/` directory and then each `.worktrees/<name>` directory under it
in sorted name order, resolving the content directory independently for
every candidate root. Where `change` is omitted, the verb SHALL default to
the currently selected spec and SHALL exit non-zero with an error when none
is selected. For each match it SHALL print a keyed block — `change:`,
`root:` (absolute path), `dir:` (the change directory relative to that
root), `status:` (the plan's status value, `?` when missing or invalid),
and, for a match from a declared project universe only, `project:` (the
owning project's slug) — with blocks separated by a blank line and the
invocation root's own match always first. When at least one match exists
the verb SHALL exit 0; when none exists it SHALL print an error naming the
probed locations and exit non-zero. The verb SHALL NOT invoke git, a
model, or the network.

#### Scenario: Local change is located
- **GIVEN** a change installed under the invocation root's `planned/`
- **WHEN** `locate <change>` runs
- **THEN** one block prints with the root, dir, and status, and the exit code
  is 0

#### Scenario: Worktree change is located
- **GIVEN** a change installed only under a worktree's own planned directory
- **WHEN** `locate <change>` runs from the main checkout
- **THEN** the printed `root:` names the worktree directory and `status:`
  carries that plan's status value

#### Scenario: Local match precedes worktree matches
- **GIVEN** the change exists in both the invocation root and a worktree
- **WHEN** `locate <change>` runs
- **THEN** the invocation root's block prints first, followed by the
  worktree's block

#### Scenario: A project-hosted change is located at workspace level
- **GIVEN** a workspace root whose declared project repo holds the change
  under its `planned/`
- **WHEN** `locate <change>` runs from the workspace root
- **THEN** the match block names that repo as `root:` and carries a
  `project: <slug>` line

#### Scenario: Universe order governs the block order
- **GIVEN** the change exists under the invocation root and under a declared
  project repo
- **WHEN** `locate <change>` runs from the workspace root
- **THEN** the invocation root's block prints first and the project block
  after it

#### Scenario: Unknown change exits non-zero
- **WHEN** `locate no-such-change` runs and no candidate root contains it
- **THEN** an error names the probed locations and the exit code is non-zero

#### Scenario: Omitted argument falls back to the current selection
- **GIVEN** a change selected via `use`
- **WHEN** `locate` runs with no argument
- **THEN** the verb locates that selected change exactly as if its name had
  been given explicitly

#### Scenario: No argument and no selection errors
- **WHEN** `locate` runs with no argument and no change is currently selected
- **THEN** the CLI exits non-zero with an error stating no change was given
  and none is selected

### Requirement: JSON output mode
id: json-output
base: 5b7c0fa479c8

The status CLI's read verbs — `show`, `status`, `locate`, `epic-show`, and
`workspace-show` — SHALL accept a `--json` flag that emits exactly one JSON
document on stdout and nothing else, derived from the same data as the text
rendering: `status` an object with `name`, `kind` (`change` or `epic`), and
`status`; `show` on a change an object with `name`, `kind`, `status`,
`tasks` (done/in_progress/total counts, or null when no checklist exists),
and `metadata`; `show`'s epic fallback and `epic-show` an object with
`name`, `kind": "epic"`, `status`, `metadata`, `worktree` (the hosting
worktree name or null), `project` (the owning declared project's slug when
the epic resolved from a project universe, else null), `shipped` counts,
and the four board `lanes` with member entries carrying `slug`, `state`,
`risk`, and a `worktree` boolean; the bare `show` workspace report an
object with `kind": "workspace"`, `totals`, `shipped`, and `lanes` whose
rows each carry a `project` field — the owning declared project's slug for
a row aggregated from a project universe, `null` for a row from the
invocation root's own universe; `locate` an array of objects with `change`,
`root`, `dir`, `status`, and `project` (the owning declared project's slug,
or `null` for a match from the invocation root's own universe); and
`workspace-show` an object mirroring the text report's fields. Without the
flag, the text output SHALL stay byte-identical to its pre-flag behavior,
and error handling (stderr `Error:` lines, exit codes) SHALL be unchanged in
both modes.

#### Scenario: Status of a change is machine-readable
- **WHEN** `status <change> --json` runs on an existing change
- **THEN** stdout parses as one JSON object with `kind` `change` and its
  status value

#### Scenario: Epic report is machine-readable
- **WHEN** `epic-show <slug> --json` runs
- **THEN** stdout parses as one JSON object with `kind` `epic`, the four
  lanes, and each member's slug, state, risk, and worktree flag

#### Scenario: A project-hosted epic's report carries its project
- **GIVEN** a workspace root whose declared project repo hosts the epic
- **WHEN** `epic-show <slug> --json` runs from the workspace root
- **THEN** the object's `project` is that project's slug, and a root-hosted
  epic's `project` is null

#### Scenario: Workspace report is machine-readable
- **WHEN** `show --json` runs with no name and no selection
- **THEN** stdout parses as one JSON object with `kind` `workspace` and the
  totals matching the text report's counts

#### Scenario: Workspace report rows carry their project
- **GIVEN** a workspace root with one declared project repo holding an epic
- **WHEN** `show --json` runs bare from the workspace root
- **THEN** the project repo's rows carry its slug in `project` and the
  invocation root's own rows carry `project` null

#### Scenario: Locate rows are an array
- **WHEN** `locate <change> --json` runs for a change hosted in a worktree
- **THEN** stdout parses as a JSON array whose entries carry change, root,
  dir, status, and a null `project`

#### Scenario: Text mode is unchanged without the flag
- **WHEN** any of the five verbs runs without `--json`
- **THEN** the output is byte-identical to the pre-change text rendering

#### Scenario: Errors are unaffected by the flag
- **WHEN** `status no-such-thing --json` runs for a name matching nothing
- **THEN** the behavior matches the flagless form (`?` on stdout per the
  status contract), and a fatal error path still prints `Error:` to stderr
  with a nonzero exit
