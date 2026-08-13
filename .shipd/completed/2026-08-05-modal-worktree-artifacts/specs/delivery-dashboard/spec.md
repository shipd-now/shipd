## ADDED Requirements

### Requirement: Worktree-aware modal artifacts
id: modal-worktree-artifacts

When the spec-detail modal resolves a member's artifact tabs, it SHALL locate
the change relative to the member's worktree-aware hosting directory (the
`location` the board aggregation derived), falling back to the invocation
root when no location is recorded — so a change planned or archived inside
its own worktree renders its Plan/Spec/Tasks tabs from the board of the main
checkout. If the located directory holds no change, then the modal SHALL show
the existing not-yet-planned notice.

#### Scenario: A worktree-planned member shows its artifacts
- **WHEN** the spec-detail modal opens for a member whose change lives only
  under `.worktrees/<slug>` (its `location`), with plan, spec, and tasks
  files present there
- **THEN** the modal renders the Plan/Spec/Tasks tabs from the worktree's
  artifact set instead of the not-yet-planned notice

#### Scenario: A root-planned member is unchanged
- **WHEN** the modal opens for a member whose change lives under the
  invocation root's own `planned/`
- **THEN** the tabs render exactly as before

#### Scenario: A missing location degrades to the notice
- **WHEN** the modal opens for a member whose recorded location no longer
  contains the change
- **THEN** the modal shows the not-yet-planned notice and raises no error
