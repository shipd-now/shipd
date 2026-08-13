## MODIFIED Requirements

### Requirement: One change per worktree and branch
id: change-worktree-isolation
base: 7fb27add0e05

Every change SHALL be developed in its own git worktree at
`.worktrees/<change>` on a branch named `change/<change>`, created via the
plugin's worktree helper (`worktree.sh` among the plugin's engine
scripts), and the entire lifecycle — planning artifacts, implementation,
verification, and the spec merge/archive — SHALL run inside that worktree
so the change's artifacts, code, and applied specs travel in a single PR.
The main checkout SHALL be used only for launching sessions, reviewing,
post-merge pulls, and the plugin snapshot refresh.

#### Scenario: Lifecycle stays in the worktree
- **WHEN** a change `dark-mode-toggle` is planned and built
- **THEN** its artifacts, implementation, verification, and merge/
  archive happen under `.worktrees/dark-mode-toggle` on branch
  `change/dark-mode-toggle`, and the main checkout's working tree is
  untouched

#### Scenario: Parallel sessions do not collide
- **WHEN** two sessions develop two different changes concurrently
- **THEN** each works in its own worktree and branch, and neither
  session's uncommitted state appears in the other's commits

## ADDED Requirements

### Requirement: Plugin-owned worktree helper
id: plugin-worktree-helper

The plugin SHALL ship the worktree helper as an engine script
(`worktree.sh` beside the other engine scripts), invocable by plugin path
in any git repository. Given a change name and run from a repository root,
the helper SHALL create the worktree at `.worktrees/<change>` on a new
branch `change/<change>` and print where to continue working; it SHALL
refuse — exiting non-zero and creating nothing — when the branch already
exists, and SHALL error when not run from a repository root (no `.git`).
The helper SHALL make no assumption about the repository beyond git
itself — no am layout, content directory, or host-repo convention is
required.

#### Scenario: Helper works in a fresh repo
- **GIVEN** a brand-new git repository with one commit and no am layout
- **WHEN** the plugin's `worktree.sh my-change` runs from its root
- **THEN** `.worktrees/my-change` exists on branch `change/my-change` and
  the exit code is zero

#### Scenario: Existing branch is refused
- **GIVEN** a repository where branch `change/my-change` already exists
- **WHEN** the helper runs with `my-change`
- **THEN** it exits non-zero and no new worktree is created

#### Scenario: Outside a repo root is an error
- **WHEN** the helper runs in a directory with no `.git`
- **THEN** it exits non-zero telling the caller to run from the repo root
