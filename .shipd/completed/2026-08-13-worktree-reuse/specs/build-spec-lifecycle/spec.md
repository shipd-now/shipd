## MODIFIED Requirements

### Requirement: Plugin-owned worktree helper
id: plugin-worktree-helper
base: fafa87162a01

The plugin SHALL ship the worktree helper as an engine script
(`worktree.sh` beside the other engine scripts), invocable by plugin path
in any git repository. Given a change name and run from a repository
root, the helper SHALL ensure a worktree exists at `.worktrees/<change>`
on branch `change/<change>` and print where to continue working, exiting
zero — creating the worktree and branch when neither exists, creating the
worktree from the existing branch when only the branch exists, and
reusing the worktree unchanged when it already exists on that branch. It
SHALL refuse — exiting non-zero and changing nothing — when
`.worktrees/<change>` exists but is checked out on a different branch,
and SHALL error when not run from a repository root. The helper SHALL
also provide `remove <change>`, which SHALL refuse — exit
code 2, listing every applicable reason — while the worktree shows work
in progress: uncommitted or untracked files, any change still under its
`.shipd/planned/`, task-claim marks (`[~]`) or a coordination lock in its
planned checklists, or any file modified within the idle window (default
30 minutes, overridable via `SHIPD_WORKTREE_IDLE_MINUTES`). When no guard
fires, `remove` SHALL remove the worktree and prune, exiting zero; a
`--force` flag SHALL override the guards but SHALL print each guard it
overrode. Workflow documentation SHALL instruct removal through this verb,
never raw `git worktree remove`. Callers SHALL NOT need to test for an
existing worktree before invoking the helper. The helper SHALL make no
assumption about the repository beyond git itself.

#### Scenario: Helper works in a fresh repo
- **GIVEN** a brand-new git repository with one commit and no am layout
- **WHEN** the plugin's `worktree.sh my-change` runs from its root
- **THEN** `.worktrees/my-change` exists on branch `change/my-change` and
  the exit code is zero

#### Scenario: Second invocation reuses the worktree
- **GIVEN** a repository where `worktree.sh my-change` has already run and
  `.worktrees/my-change` is checked out on `change/my-change`
- **WHEN** `worktree.sh my-change` runs again
- **THEN** the exit code is zero, the worktree is still present on that
  branch, and its working tree is unchanged

#### Scenario: Existing branch without a worktree is re-attached
- **GIVEN** a repository where branch `change/my-change` exists but
  `.worktrees/my-change` does not
- **WHEN** `worktree.sh my-change` runs
- **THEN** `.worktrees/my-change` is created on that existing branch and
  the exit code is zero

#### Scenario: A worktree on a different branch is refused
- **GIVEN** a repository where `.worktrees/my-change` exists but is
  checked out on a branch other than `change/my-change`
- **WHEN** `worktree.sh my-change` runs
- **THEN** it exits non-zero and neither the worktree nor any branch is
  changed

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

#### Scenario: Re-entry after removal succeeds
- **GIVEN** a change whose worktree was removed by `remove my-change`
  while its branch `change/my-change` remains
- **WHEN** `worktree.sh my-change` runs again
- **THEN** the worktree is recreated on that branch and the exit code is
  zero
