## ADDED Requirements

### Requirement: Main-checkout epic write warning
id: main-checkout-epic-write-warning

When `epic-sync` or `epic-set-status` actually modifies an epic file and the
repository root's `.git` is a directory (a main checkout rather than a
linked worktree), the CLI SHALL print a one-line warning to stderr naming
the modified file and stating that a protected-main workflow must ship the
change via a worktree PR. The warning SHALL NOT change exit codes or block
the write, SHALL NOT appear when the same write happens in a linked
worktree (`.git` is a file), and SHALL NOT appear when a sync derives no
status change and writes nothing.

#### Scenario: Main-checkout write warns
- **GIVEN** a repo fixture whose root `.git` is a directory
- **WHEN** `epic-set-status active` rewrites an epic's status line
- **THEN** stderr carries the one-line warning naming the epic file and the
  exit code is zero

#### Scenario: Worktree write stays silent
- **GIVEN** a repo fixture whose root `.git` is a file
- **WHEN** `epic-set-status active` rewrites an epic's status line
- **THEN** no warning is emitted

#### Scenario: No-op sync stays silent
- **GIVEN** a main-checkout fixture whose epic already carries its derived
  status
- **WHEN** `epic-sync` runs
- **THEN** nothing is written and no warning is emitted
