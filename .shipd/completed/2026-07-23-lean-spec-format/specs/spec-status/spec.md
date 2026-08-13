# spec-status — delta

## MODIFIED Requirements

### Requirement: Plan status header
id: proposal-status-header
base: 0ceb5b57808a

Every change's `plan.md` SHALL begin with a `# <change-name>` title on line 1,
where `<change-name>` equals the change's directory slug, and SHALL carry a
`Status: <status>` line as the first non-blank line after the title.
`<status>` SHALL be exactly one of `draft`, `ready`, `active`, `complete`,
`verified`.

#### Scenario: Header shape
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` starts with `# dark-mode-toggle` followed by a line
  `Status: draft` before any other content

#### Scenario: Only the five statuses are valid
- **WHEN** a `Status:` line carries any value other than draft, ready,
  active, complete, or verified
- **THEN** tooling treats the status as invalid

### Requirement: Status CLI
id: status-cli
base: 11280bfc0c65

A stdlib-Python CLI SHALL provide: `show [change]` printing the change's
status and task progress; `status [change]` printing the bare status value
(`?` when missing or invalid); `validate [change]` checking the change's
structural validity and exiting non-zero with the errors when invalid;
`set-status <status> [change]` writing a validated status value into the
`plan.md` header (inserting the header if absent) subject to the transition
guards; and `sync [change]` re-deriving the status from `tasks.md` — mapping
all-done to `complete`, any-done-or-in-progress to `active`, and none-started
to `ready` — while never changing a status of `draft` or `verified`. No
unguarded setter SHALL exist. Where `[change]` is omitted, the CLI SHALL
default to the currently selected spec and SHALL exit non-zero with an error
when none is selected.

#### Scenario: Sync derives active
- **GIVEN** a change with status `ready`
- **WHEN** `sync` runs after one task is marked done
- **THEN** the plan's status line becomes `active`

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
- **WHEN** `status` runs on a change whose plan header is valid
- **THEN** stdout is exactly the status value
