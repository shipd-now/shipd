## ADDED Requirements

### Requirement: Proposal status header
id: proposal-status-header

Every change's `proposal.md` SHALL begin with a `# <change-name>` title on
line 1, where `<change-name>` equals the change's directory slug, and SHALL
carry a `Status: <status>` line as the first non-blank line after the title.
`<status>` SHALL be exactly one of `draft`, `ready`, `active`, `complete`,
`verified`.

#### Scenario: Header shape
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `proposal.md` starts with `# dark-mode-toggle` followed by a
  line `Status: draft` before any other content

#### Scenario: Only the five statuses are valid
- **WHEN** a `Status:` line carries any value other than draft, ready,
  active, complete, or verified
- **THEN** tooling treats the status as invalid

### Requirement: Status lifecycle stages
id: status-lifecycle-stages

The five statuses SHALL denote pipeline stages with these semantics: `draft` —
the spec is being authored and may be incomplete; `ready` — the spec is
lint-clean and approved but no task has been worked on; `active` — at least
one task is done or in progress; `complete` — every task is done; `verified` —
the completed work has been checked against the spec.

#### Scenario: Stages reflect task state
- **WHEN** a change's `tasks.md` shows some but not all tasks done
- **THEN** the change's pipeline stage is `active`

#### Scenario: Verified means checked, not merely done
- **WHEN** all tasks are done but verification has not been performed
- **THEN** the stage is `complete`, and it becomes `verified` only once the
  work has been verified against the spec

### Requirement: Pipeline-owned transitions with manual override
id: pipeline-owned-transitions

The planning and build flows SHALL drive status transitions automatically:
planning emits `draft` and promotes to `ready` at the approval gate; the build
flow sets `active` when execution starts, `complete` when the task checklist
shows nothing pending or in progress, and `verified` when verification passes.
The status CLI SHALL additionally allow setting any status explicitly at any
time.

#### Scenario: Approval promotes draft to ready
- **WHEN** an authored change passes lint and the user approves the plan
- **THEN** the pipeline sets its status to `ready` without manual editing

#### Scenario: Manual override is allowed
- **WHEN** a user explicitly sets a change's status to any of the five values
- **THEN** the status line is updated to that value regardless of derived
  state

### Requirement: Status CLI
id: status-cli

A stdlib-Python CLI SHALL provide: `show [change]` printing the change's
status and task progress; `set <status> [change]` writing a validated status
value into the proposal header (inserting the header if absent); and
`sync [change]` re-deriving the status from `tasks.md` — mapping all-done to
`complete`, any-done-or-in-progress to `active`, and none-started to `ready` —
while never changing a status of `draft` or `verified`. Where `[change]` is
omitted, the CLI SHALL default to the currently selected spec and SHALL exit
non-zero with an error when none is selected.

#### Scenario: Sync derives active
- **GIVEN** a change with status `ready`
- **WHEN** `sync` runs after one task is marked done
- **THEN** the proposal's status line becomes `active`

#### Scenario: Sync never touches draft or verified
- **WHEN** `sync` runs on a change whose status is `draft` or `verified`
- **THEN** the status line is left unchanged

#### Scenario: Set validates the value
- **WHEN** `set` is invoked with a value outside the five statuses
- **THEN** the CLI writes nothing and exits non-zero with an error
