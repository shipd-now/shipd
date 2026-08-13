## MODIFIED Requirements

### Requirement: Epic status verbs
id: epic-status-verbs
base: 89c16f76c216

The status CLI SHALL provide `epic-show <slug>` printing an epic's status,
metadata, and one line per stub member with its derived state; `epic-sync
<slug>` re-deriving the epic's status from member states; and
`epic-set-status <status> <slug>` writing a validated epic status
(`draft`, `ready`, `active`, `complete`), refusing `ready` unless the epic
lints clean, with refusals printing a `Refused: ` reason and exiting 3. A
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

#### Scenario: A member absent everywhere is still unplanned
- **GIVEN** a member with no change under the invocation root and none under any
  worktree
- **WHEN** the member's state is derived
- **THEN** the state is `unplanned`

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
