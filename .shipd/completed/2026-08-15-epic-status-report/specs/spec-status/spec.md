## MODIFIED Requirements

### Requirement: Status CLI
id: status-cli
base: a01c7db87286

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
spec and SHALL exit non-zero with an error when none is selected. When the
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

### Requirement: Epic status verbs
id: epic-status-verbs
base: 9fe0b50e052a

The status CLI SHALL provide `epic-show <slug>` printing the epic's
board-shaped report; `epic-sync <slug>` re-deriving the epic's status from
member states; and `epic-set-status <status> <slug>` writing a validated
epic status (`draft`, `ready`, `active`, `complete`), refusing `ready`
unless the epic lints clean, with refusals printing a `Refused: ` reason
and exiting 3. The board-shaped report SHALL print, in order: the
`<slug>: <status>` line and the epic's header metadata lines (unchanged
from before this report existed); a `shipped <n>/<m>` line where `n` is
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

### Requirement: Interactive status skill
id: interactive-status-skill
base: f9cbcfb13f84

An `am:status` skill SHALL expose three commands over the status CLI —
`status` (report the selected or named change's status), `validate` (report
structural validity or the errors), and `set-status <status>` (guarded
transition). When the `status` command's argument names an epic rather than
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
