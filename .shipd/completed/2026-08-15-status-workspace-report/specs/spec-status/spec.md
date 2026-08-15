## ADDED Requirements

### Requirement: Workspace board report
id: workspace-board-report

When `show` runs with no name given and no spec selected, the status CLI
SHALL print a workspace board report derived from the spec tree alone, in
order: a `N specs · N epics · N initiatives` totals line — members summed
across every epic, the epic count, and the distinct `Initiative:` slugs
across epic files, matching the board header's totals; a `shipped <n>/<m>`
line over every rendered row (epic members plus standalone changes), `n`
counting those whose lane is `shipped`; a blank line; then the four board
lanes in board order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each
printed as a `<LANE> (<count>)` header even when its count is 0. In the
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

#### Scenario: A selection still wins
- **GIVEN** a selected change
- **WHEN** `show` runs with no argument
- **THEN** the change's one-liner is printed, not the workspace report

## MODIFIED Requirements

### Requirement: Status CLI
id: status-cli
base: fa38b21b51e3

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
given name matches no change but an epic of that slug exists, `status`
SHALL print the epic's status value and `show` SHALL print the epic's
board-shaped report — identical to `epic-show`'s output; a name matching
neither a change nor an epic SHALL keep printing `?` from `status`.

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

#### Scenario: A name that is neither change nor epic stays a question mark
- **WHEN** `status <name>` runs for a name matching no change and no epic
- **THEN** `?` is printed

#### Scenario: Bare status without a selection still errors
- **GIVEN** no spec selected
- **WHEN** `status` runs with no argument
- **THEN** the CLI exits non-zero with the no-selection error

### Requirement: Interactive status skill
id: interactive-status-skill
base: 11ddc41b2823

An `am:status` skill SHALL expose three commands over the status CLI —
`status` (report the selected or named change's status), `validate` (report
structural validity or the errors), and `set-status <status>` (guarded
transition). When invoked with no argument, the skill SHALL run `show`
alone and relay its output — the selected change's one-liner when a
selection exists, else the CLI's workspace board report — never surfacing
the bare `status` verb's no-selection error as the answer. When the
`status` command's argument names an epic rather than
a change, the skill SHALL relay the CLI's board-shaped epic report and point
epic transitions at the epic verbs rather than `set-status`. When
`set-status` is refused by a guard (exit code 3), the skill
SHALL surface the refusal reason and ask the user whether to override,
re-running with `--force` only after explicit consent; it SHALL never pass
`--force` uninvited, and on decline SHALL leave the status unchanged.

#### Scenario: Refusal asks before forcing
- **WHEN** the skill's `set-status complete` is refused because tickets are
  open
- **THEN** the skill shows the reason, asks the user, and only re-runs with
  `--force` if the user chooses to override

#### Scenario: Decline leaves the status untouched
- **WHEN** the user declines the override question
- **THEN** the proposal's status line is unchanged and the skill reports the
  refusal

#### Scenario: An epic argument reports the epic
- **WHEN** the skill's `status` command is invoked with an epic's slug
- **THEN** the skill relays the board-shaped epic report instead of a
  change status

#### Scenario: A bare invocation reports the workspace
- **GIVEN** no spec selected
- **WHEN** the skill is invoked with no argument
- **THEN** the skill relays the CLI's workspace board report rather than
  the no-selection error
