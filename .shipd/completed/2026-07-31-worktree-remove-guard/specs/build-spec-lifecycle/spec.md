## MODIFIED Requirements

### Requirement: Plugin-owned worktree helper
id: plugin-worktree-helper
base: defcf9ecde90

The plugin SHALL ship the worktree helper as an engine script
(`worktree.sh` beside the other engine scripts), invocable by plugin path
in any git repository. Given a change name and run from a repository
root, the helper SHALL create the worktree at `.worktrees/<change>` on a
new branch `change/<change>` and print where to continue working; it
SHALL refuse — exiting non-zero and creating nothing — when the branch
already exists, and SHALL error when not run from a repository root. The
helper SHALL also provide `remove <change>`, which SHALL refuse — exit
code 2, listing every applicable reason — while the worktree shows work
in progress: uncommitted or untracked files, any change still under its
`.shipd/planned/`, task-claim marks (`[~]`) or a coordination lock in its
planned checklists, or any file modified within the idle window (default
30 minutes, overridable via `SHIPD_WORKTREE_IDLE_MINUTES`). When no guard
fires, `remove` SHALL remove the worktree and prune, exiting zero; a
`--force` flag SHALL override the guards but SHALL print each guard it
overrode. Workflow documentation SHALL instruct removal through this verb,
never raw `git worktree remove`. The helper SHALL make no assumption
about the repository beyond git itself.

#### Scenario: Helper works in a fresh repo
- **GIVEN** a brand-new git repository with one commit and no am layout
- **WHEN** the plugin's `worktree.sh my-change` runs from its root
- **THEN** `.worktrees/my-change` exists on branch `change/my-change` and
  the exit code is zero

#### Scenario: Existing branch is refused
- **GIVEN** a repository where branch `change/my-change` already exists
- **WHEN** the helper runs with `my-change`
- **THEN** it exits non-zero and no new worktree is created

#### Scenario: Clean cold worktree removes
- **GIVEN** a worktree with a clean tree, nothing under `.shipd/planned/`,
  no claims, and no file touched inside the idle window
- **WHEN** `remove my-change` runs
- **THEN** the worktree is gone and the exit code is zero

#### Scenario: In-progress work refuses removal
- **GIVEN** a worktree carrying an unshipped change under `.shipd/planned/`
  and a `[~]` claim in its tasks.md
- **WHEN** `remove my-change` runs without `--force`
- **THEN** nothing is removed, both reasons are listed, and the exit code
  is 2

#### Scenario: Fresh activity refuses removal
- **GIVEN** an otherwise clean worktree with a file modified two minutes
  ago
- **WHEN** `remove my-change` runs
- **THEN** the refusal names the recent-activity guard and nothing is
  removed

#### Scenario: Force overrides audibly
- **WHEN** `remove my-change --force` runs against a worktree with a
  dirty tree
- **THEN** the worktree is removed and the output names the dirty-tree
  guard as overridden
