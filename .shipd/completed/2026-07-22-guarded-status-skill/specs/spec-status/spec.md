## ADDED Requirements

### Requirement: Transition guards
id: transition-guards

`set-status` SHALL enforce guards derived from the target status before
writing: targeting `draft` requires nothing; targeting `ready` or `active`
requires the change to pass structural validation; targeting `complete` or
`verified` additionally requires a finished checklist — `tasks.md` present
with at least one checkbox and nothing pending or in progress. A refused
transition SHALL write nothing, print a reason line beginning `Refused: ` to
stderr (with concrete task counts or the validation errors), and exit with
code 3, distinct from general errors. A `--force` flag SHALL bypass the
guards but SHALL NOT bypass status-value validation.

#### Scenario: Complete refused while tickets are open
- **GIVEN** a change with 7 of 10 tasks done
- **WHEN** `set-status complete` runs without `--force`
- **THEN** nothing is written, stderr starts `Refused: `, and the exit code
  is 3

#### Scenario: Ready refused when the spec does not validate
- **WHEN** `set-status ready` runs on a change whose delta specs fail
  structural validation
- **THEN** the transition is refused with the validation errors and exit
  code 3

#### Scenario: Force bypasses guards after consent
- **WHEN** `set-status complete --force` runs on a change with open tasks
- **THEN** the status line is written to `complete` and the exit code is 0

#### Scenario: Force never accepts an invalid value
- **WHEN** `set-status done --force` runs
- **THEN** nothing is written and the CLI errors with exit code 1

### Requirement: Interactive status skill
id: interactive-status-skill

An `am:status` skill SHALL expose three commands over the status CLI —
`status` (report the selected or named change's status), `validate` (report
structural validity or the errors), and `set-status <status>` (guarded
transition). When `set-status` is refused by a guard (exit code 3), the skill
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

## MODIFIED Requirements

### Requirement: Status CLI
id: status-cli
base: 1abf91db4d11

A stdlib-Python CLI SHALL provide: `show [change]` printing the change's
status and task progress; `status [change]` printing the bare status value
(`?` when missing or invalid); `validate [change]` checking the change's
structural validity and exiting non-zero with the errors when invalid;
`set-status <status> [change]` writing a validated status value into the
proposal header (inserting the header if absent) subject to the transition
guards; and `sync [change]` re-deriving the status from `tasks.md` — mapping
all-done to `complete`, any-done-or-in-progress to `active`, and none-started
to `ready` — while never changing a status of `draft` or `verified`. No
unguarded setter SHALL exist. Where `[change]` is omitted, the CLI SHALL
default to the currently selected spec and SHALL exit non-zero with an error
when none is selected.

#### Scenario: Sync derives active
- **GIVEN** a change with status `ready`
- **WHEN** `sync` runs after one task is marked done
- **THEN** the proposal's status line becomes `active`

#### Scenario: Sync never touches draft or verified
- **WHEN** `sync` runs on a change whose status is `draft` or `verified`
- **THEN** the status line is left unchanged

#### Scenario: Set-status validates the value
- **WHEN** `set-status` is invoked with a value outside the five statuses
- **THEN** the CLI writes nothing and exits non-zero with an error

#### Scenario: Validate reports structural errors
- **WHEN** `validate` runs on a change whose artifacts violate the spec
  grammar
- **THEN** the errors are printed and the exit code is non-zero

#### Scenario: Bare status is scriptable
- **WHEN** `status` runs on a change whose proposal header is valid
- **THEN** stdout is exactly the status value

### Requirement: Pipeline-owned transitions with manual override
id: pipeline-owned-transitions
base: ead93583af5d

The planning and build flows SHALL drive status transitions automatically via
the guarded `set-status` verb: planning emits `draft` and promotes to `ready`
at the approval gate; the build flow sets `active` when execution starts,
`complete` when the task checklist shows nothing pending or in progress, and
`verified` when verification passes. Explicit manual overrides SHALL remain
possible through `set-status --force`, gated on user consent when driven
through the interactive skill.

#### Scenario: Approval promotes draft to ready
- **WHEN** an authored change passes lint and the user approves the plan
- **THEN** the pipeline sets its status to `ready` without manual editing and
  without `--force`

#### Scenario: Manual override is allowed
- **WHEN** a user explicitly sets a change's status with `--force`
- **THEN** the status line is updated to that value regardless of derived
  state
