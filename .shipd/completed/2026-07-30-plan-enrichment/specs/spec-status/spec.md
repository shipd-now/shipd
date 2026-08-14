## ADDED Requirements

### Requirement: Locate verb
id: locate-verb

The status CLI SHALL provide `locate <change>` searching for an installed
change by probing the invocation root's resolved `planned/` directory and then
each `.worktrees/<name>` directory under the invocation root in sorted name
order, resolving the content directory independently for every candidate root.
For each match it SHALL print a keyed block — `change:`, `root:` (absolute
path), `dir:` (the change directory relative to that root), and `status:` (the
plan's status value, `?` when missing or invalid) — with blocks separated by a
blank line and the invocation root's own match always first. When at least one
match exists the verb SHALL exit 0; when none exists it SHALL print an error
naming the probed locations and exit non-zero. The verb SHALL NOT invoke git,
a model, or the network.

#### Scenario: Local change is located
- **GIVEN** a change installed under the invocation root's `planned/`
- **WHEN** `locate <change>` runs
- **THEN** one block prints with the root, dir, and status, and the exit code
  is 0

#### Scenario: Worktree change is located
- **GIVEN** a change installed only under a worktree's own planned directory
- **WHEN** `locate <change>` runs from the main checkout
- **THEN** the printed `root:` names the worktree directory and `status:`
  carries that plan's status value

#### Scenario: Local match precedes worktree matches
- **GIVEN** the change exists in both the invocation root and a worktree
- **WHEN** `locate <change>` runs
- **THEN** the invocation root's block prints first, followed by the
  worktree's block

#### Scenario: Unknown change exits non-zero
- **WHEN** `locate no-such-change` runs and no candidate root contains it
- **THEN** an error names the probed locations and the exit code is non-zero
