## ADDED Requirements

### Requirement: Sub-agent workspace gate
id: subagent-workspace-gate

The execution sub-agent role contract (`agents/sub-agent.md`) SHALL require
a workspace gate the sub-agent passes **before its first claim or file
edit**: confirm the working directory is the worktree root named in the
spawn message, and confirm `git rev-parse --abbrev-ref HEAD` prints
`change/<change>` for the spawned change; if either check fails, then the
sub-agent SHALL stop and report the mismatch instead of claiming, editing,
or changing directory elsewhere. The contract SHALL also require that every
file path the sub-agent edits or passes to commands stays inside that
worktree root — never an absolute path into another checkout.

#### Scenario: The contract carries the gate
- **WHEN** `agents/sub-agent.md` is read
- **THEN** it contains a workspace-gate section requiring the worktree-root
  and `git rev-parse --abbrev-ref HEAD` checks before the first claim or
  edit, the stop-and-report-on-mismatch rule, and the paths-inside-the-
  worktree rule

#### Scenario: The gate is covered by a stdlib test
- **WHEN** the engine test suite runs without `textual`
- **THEN** a test asserts the contract file carries the gate's required
  elements, so a contract regression fails CI
