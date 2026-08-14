## ADDED Requirements

### Requirement: Epic status verbs
id: epic-status-verbs

The status CLI SHALL provide `epic-show <slug>` printing an epic's status,
metadata, and one line per stub member with its derived state; `epic-sync
<slug>` re-deriving the epic's status from member states; and
`epic-set-status <status> <slug>` writing a validated epic status
(`draft`, `ready`, `active`, `complete`), refusing `ready` unless the epic
lints clean, with refusals printing a `Refused: ` reason and exiting 3. A
member's state SHALL be `archived` when a matching `am/completed/*-<slug>/`
exists, else the member change's plan status when `am/planned/<slug>/`
exists, else `unplanned`. `epic-sync` SHALL derive: all members archived →
`complete`; any member archived or with plan status `active`, `complete`, or
`verified` → `active`; otherwise `ready` — and SHALL never change an epic
whose status is `draft`.

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

#### Scenario: Ready is guarded by lint
- **WHEN** `epic-set-status ready` runs on an epic that fails structural
  validation
- **THEN** nothing is written, stderr starts `Refused: `, and the exit code
  is 3

#### Scenario: Show lists member states
- **WHEN** `epic-show` runs on an epic with an archived member, a planned
  member, and an unplanned stub
- **THEN** the output lists each member with `archived`, its plan status, and
  `unplanned` respectively
