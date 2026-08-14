## MODIFIED Requirements

### Requirement: Plan status header
id: proposal-status-header
base: 1ce6f0921d50

Every change's `plan.md` SHALL begin with a `# <change-name>` title on line
1, where `<change-name>` equals the change's directory slug, and SHALL
carry a `Status: <status>` line as the first non-blank line after the
title. `<status>` SHALL be exactly one of `draft`, `ready`, `active`,
`complete`, `verified`, `rejected`.

#### Scenario: Header shape
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` starts with `# dark-mode-toggle` followed by a
  line `Status: draft` before any other content

#### Scenario: Only the six statuses are valid
- **WHEN** a `Status:` line carries any value other than draft, ready,
  active, complete, verified, or rejected
- **THEN** tooling treats the status as invalid

### Requirement: Status lifecycle stages
id: status-lifecycle-stages
base: 109c68b7cd14

The six statuses SHALL denote pipeline stages with these semantics:
`draft` — the spec is being authored and may be incomplete; `ready` — the
spec is lint-clean and approved but no task has been worked on; `active` —
at least one task is done or in progress; `complete` — every task is done;
`verified` — the completed work has been checked against the spec;
`rejected` — the context-sufficiency gate found the plan lacking context
to build against the codebase, and it is parked for human enrichment.
`rejected` SHALL be entered by the gate (from `draft` or `ready`) and
exited by a human transition back to `draft` or `ready` after enrichment.

#### Scenario: Stages reflect task state
- **WHEN** a change's `tasks.md` shows some but not all tasks done
- **THEN** the change's pipeline stage is `active`

#### Scenario: Verified means checked, not merely done
- **WHEN** all tasks are done but verification has not been performed
- **THEN** the stage is `complete`, and it becomes `verified` only once
  the work has been verified against the spec

#### Scenario: Rejected means parked for enrichment
- **WHEN** the gate rejects a plan and a human later enriches it
- **THEN** the plan sits at `rejected` in between, and returns to the
  pipeline via `draft` or `ready`

### Requirement: Transition guards
id: transition-guards
base: cd3908d4c233

`set-status` SHALL enforce guards derived from the target status before
writing: targeting `draft` or `rejected` requires nothing; targeting
`ready` or `active` requires the change to pass structural validation;
targeting `complete` or `verified` additionally requires a finished
checklist — `tasks.md` present with at least one checkbox and nothing
pending or in progress. A refused transition SHALL write nothing, print a
reason line beginning `Refused: ` to stderr (with concrete task counts or
the validation errors), and exit with code 3, distinct from general
errors. A `--force` flag SHALL bypass the guards but SHALL NOT bypass
status-value validation.

#### Scenario: Complete refused while tickets are open
- **GIVEN** a change with 7 of 10 tasks done
- **WHEN** `set-status complete` runs without `--force`
- **THEN** nothing is written, stderr starts `Refused: `, and the exit
  code is 3

#### Scenario: Rejected needs no structural validity
- **WHEN** `set-status rejected` runs on a change whose delta specs fail
  structural validation
- **THEN** the status line is written to `rejected` and the exit code is 0

#### Scenario: Force never accepts an invalid value
- **WHEN** `set-status done --force` runs
- **THEN** nothing is written and the CLI errors with exit code 1

### Requirement: Status CLI
id: status-cli
base: a578753c8fbd

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
spec and SHALL exit non-zero with an error when none is selected.

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
