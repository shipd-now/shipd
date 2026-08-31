## MODIFIED Requirements

### Requirement: Plugin-owned worktree helper
id: plugin-worktree-helper
base: 9950d221c31d

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
planned checklists, or — **only while the worktree's tree is dirty** — any
file modified within the idle window (default 30 minutes, overridable via
`SHIPD_WORKTREE_IDLE_MINUTES`). Where the tree is clean, the idle probe
SHALL NOT run and SHALL NOT contribute a reason, so a worktree whose work
is fully committed removes however recently its files were written. The
unshipped-change guard SHALL NOT fire for a planned change directory that
is base content rather than the worktree's own work — one that is
tracked, has no local modifications or untracked files, and is
byte-identical to the same path on the base branch (the helper's resolved
base: the root checkout's currently checked-out branch); where no base
resolves, or the base is the worktree's own branch, the carve-out SHALL
NOT apply and every planned change guards as before. The task-claim and
coordination-lock guard SHALL keep scanning every planned checklist,
base-tracked or not. When no guard
fires, `remove` SHALL remove the worktree and prune, exiting zero; a
`--force` flag SHALL override the guards but SHALL print each guard it
overrode. Workflow documentation SHALL instruct removal through this verb,
never raw `git worktree remove`. Callers SHALL NOT need to test for an
existing worktree before invoking the helper. The helper SHALL make no
assumption about the repository beyond git itself.

#### Scenario: Helper works in a fresh repo
- **GIVEN** a brand-new git repository with one commit and no shipd layout
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

#### Scenario: A just-finished clean worktree removes without --force
- **GIVEN** a worktree whose files were all written and committed seconds
  ago, with a clean tree, nothing under `.shipd/planned/`, and no claims
- **WHEN** `remove my-change` runs with no `--force` and the default idle
  window
- **THEN** the worktree is gone, the exit code is zero, and no reason
  naming the idle window is printed

#### Scenario: In-progress work refuses removal
- **GIVEN** a worktree carrying an unshipped change under `.shipd/planned/`
  and a `[~]` claim in its tasks.md
- **WHEN** `remove my-change` runs without `--force`
- **THEN** nothing is removed, both reasons are listed, and the exit code
  is 2

#### Scenario: Base-tracked planned content does not guard
- **GIVEN** a repository whose base branch carries
  `.shipd/planned/other-change/` and a worktree checked out from it with
  that directory unmodified, otherwise clean and idle
- **WHEN** `remove my-change` runs without `--force`
- **THEN** the worktree is removed and the exit code is zero

#### Scenario: A modified base-tracked planned change still guards
- **GIVEN** the same repository, with one file under
  `.shipd/planned/other-change/` edited inside the worktree
- **WHEN** `remove my-change` runs without `--force`
- **THEN** the refusal lists the unshipped-change reason and nothing is
  removed

#### Scenario: A claim in base-tracked planned content still guards
- **GIVEN** the same repository, where the base branch's
  `.shipd/planned/other-change/tasks.md` itself carries a `[~]` mark
- **WHEN** `remove my-change` runs without `--force`
- **THEN** the refusal lists the task-claim reason

#### Scenario: Detached base applies no carve-out
- **GIVEN** the same repository with the root checkout's HEAD detached
- **WHEN** `remove my-change` runs without `--force`
- **THEN** the refusal lists the unshipped-change reason for the
  base-tracked planned change, exactly as before the carve-out

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

### Requirement: Guarded pruning of merged change branches
id: prune-merged-change-branches
base: 529fbdc473c3

The worktree helper SHALL provide a `prune-branches` verb that, run from the
repository root, deletes every local `change/*` branch whose content is merged
into the base branch and SHALL never delete the root checkout's current
branch, any branch checked out in a worktree, any unmerged branch, or any
branch outside `change/*`. Merged-ness SHALL be judged by two probes in
order: the content-based, squash-aware probe the fresh-branch flag uses;
and, where that probe reports not-merged, whether the branch's
remote-tracking ref is absent — the state a squash merge that deletes its
remote branch leaves. Because the content probe compares patch identities
against the base, it SHALL NOT be relied on alone: a branch whose base
moved between its fork point and its merge yields a different patch and is
otherwise mis-reported as unmerged. Where a remote is configured, the verb
SHALL refresh the remote-tracking refs (a pruning fetch) before the second
probe, and SHALL fall back to the first probe's verdict alone where no
remote is configured or the refresh fails, so the verb never depends on
network availability. It SHALL print one line per deleted branch and one
per kept candidate with the reason, and SHALL exit zero whether or not
anything was deleted. If the root checkout's HEAD is detached, then the verb
SHALL error exiting non-zero.

#### Scenario: Squash-merged local branches are pruned and listed
- **GIVEN** local branches `change/a` and `change/b` whose content was
  squash-merged into the base branch, with no worktrees attached
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** both branches are deleted, each named on a `pruned:` line, and the
  exit code is zero

#### Scenario: A branch merged onto a moved base is pruned
- **GIVEN** a local `change/a` whose content was squash-merged into the base
  after an unrelated commit touching the same files had already landed there,
  so the content probe reports it unmerged, and whose remote branch was
  deleted by that merge
- **WHEN** `worktree.sh prune-branches` runs against a repository whose
  remote no longer carries the branch
- **THEN** `change/a` is deleted and named on a `pruned:` line, and the exit
  code is zero

#### Scenario: A remote-less repository still prunes by content
- **GIVEN** a repository with no remote configured and a `change/a` whose
  content was squash-merged into the base with the base unmoved
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** `change/a` is deleted, no error about a missing remote is printed,
  and the exit code is zero

#### Scenario: A branch whose remote ref survives is kept
- **GIVEN** a local `change/a` that the content probe reports unmerged and
  whose remote-tracking ref still exists
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** `change/a` still exists, named on a `kept:` line, and the exit
  code is zero

#### Scenario: Unmerged and checked-out branches survive
- **GIVEN** an unmerged `change/wip` and a `change/active` checked out in
  `.worktrees/active`
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** both branches still exist, each named on a `kept:` line with its
  reason, and the exit code is zero

#### Scenario: Nothing to prune still exits zero
- **GIVEN** no local `change/*` branch is merged into the base branch
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** no branch is deleted and the exit code is zero
