## MODIFIED Requirements

### Requirement: Workspace board report
id: workspace-board-report
base: dd633d51d195

When `show` runs with no name given and no spec selected, the status CLI
SHALL print a workspace board report derived from the spec tree alone, in
order: a `N specs · N epics · N initiatives` totals line — members summed
across every epic, the epic count, and the distinct `Initiative:` slugs
across epic files, matching the board header's totals; a `shipped <n>/<m>`
line over every rendered row (epic members plus standalone changes), `n`
counting those whose lane is `shipped`; a blank line; then the four board
lanes in board order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each
printed as a `<LANE> (<count>)` header even when its count is 0.

The report SHALL aggregate one or more universes. The invocation root's own
universe is always aggregated: its epics discovered by probing the invocation
root first, then each `.worktrees/<name>` directory under it in sorted name
order — resolving each candidate's content directory independently, skipping
unreadable candidates, the invocation root winning a slug hosted in both —
each epic read from its hosting root. Where a workspace project registry is
discoverable from the invocation root AND the invocation root lies inside no
declared project repo (project resolution yields the implicit default), the
report SHALL additionally aggregate one universe per declared project repo
directory present on disk — projects in slug order, a project's repos in
declaration order — each repo aggregated exactly as an invocation root is
(its own epics, worktrees, member-state derivation, and standalone-change
discovery, all relative to that repo). A repo entry whose path is not a
directory, duplicates an earlier entry's real path, or resolves to the
invocation root itself SHALL be skipped, never raised. When no registry is
discoverable, or the invocation root lies inside a declared project repo,
the report SHALL cover only the invocation root's universe and its output
SHALL be byte-identical to the single-universe rendering. Epic slugs SHALL
NOT be deduplicated across universes; totals sum across every universe and
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

### Requirement: JSON output mode
id: json-output
base: afc2ea98a150

The status CLI's read verbs — `show`, `status`, `locate`, `epic-show`, and
`workspace-show` — SHALL accept a `--json` flag that emits exactly one JSON
document on stdout and nothing else, derived from the same data as the text
rendering: `status` an object with `name`, `kind` (`change` or `epic`), and
`status`; `show` on a change an object with `name`, `kind`, `status`,
`tasks` (done/in_progress/total counts, or null when no checklist exists),
and `metadata`; `show`'s epic fallback and `epic-show` an object with
`name`, `kind": "epic"`, `status`, `metadata`, `worktree` (the hosting
worktree name or null), `shipped` counts, and the four board `lanes` with
member entries carrying `slug`, `state`, `risk`, and a `worktree` boolean;
the bare `show` workspace report an object with `kind": "workspace"`,
`totals`, `shipped`, and `lanes` whose rows each carry a `project` field —
the owning declared project's slug for a row aggregated from a project
universe, `null` for a row from the invocation root's own universe; `locate`
an array of objects with `change`, `root`, `dir`, and `status`; and
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
  dir, and status

#### Scenario: Text mode is unchanged without the flag
- **WHEN** any of the five verbs runs without `--json`
- **THEN** the output is byte-identical to the pre-change text rendering

#### Scenario: Errors are unaffected by the flag
- **WHEN** `status no-such-thing --json` runs for a name matching nothing
- **THEN** the behavior matches the flagless form (`?` on stdout per the
  status contract), and a fatal error path still prints `Error:` to stderr
  with a nonzero exit
