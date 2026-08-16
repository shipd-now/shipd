## ADDED Requirements

### Requirement: Loud branch reuse in the worktree helper
id: loud-branch-reuse

When the worktree helper's create path reuses existing state — the worktree
already present on `change/<name>`, or the branch existing without a worktree —
it SHALL print an explicit reuse notice naming the reused worktree or branch
together with the branch's ahead/behind counts against the base branch (the
root checkout's currently checked-out branch), and SHALL NOT announce the
worktree as created; only the arm that creates both worktree and branch SHALL
print the created message. If the root checkout's HEAD is detached, then the
notice SHALL still print without the counts.

#### Scenario: Reused worktree is announced with counts
- **GIVEN** `.worktrees/my-change` already exists on `change/my-change`, one
  commit ahead of and one behind the base branch
- **WHEN** `worktree.sh my-change` runs again
- **THEN** stdout carries a reuse notice naming the worktree and
  `(ahead 1, behind 1` against the base branch, and no created message

#### Scenario: Re-attached branch is announced with counts
- **GIVEN** branch `change/my-change` exists with no worktree
- **WHEN** `worktree.sh my-change` runs
- **THEN** stdout carries an attach notice naming the existing branch with its
  ahead/behind counts, and no created message

#### Scenario: True creation still says created
- **GIVEN** neither `.worktrees/my-change` nor `change/my-change` exists
- **WHEN** `worktree.sh my-change` runs
- **THEN** stdout announces the created worktree and prints no reuse notice

### Requirement: Fresh-branch flag on the worktree helper
id: worktree-fresh-flag

Where the worktree helper's create path is invoked with `--fresh`, it SHALL
guarantee a fresh branch: if `.worktrees/<name>` already exists, then it SHALL
error exiting non-zero changing nothing; if `change/<name>` exists and its
content is not merged into the base branch, then it SHALL error exiting
non-zero naming the unmerged branch and changing nothing; if `change/<name>`
exists and its content is merged into the base branch (a squash merge counts
as merged), then it SHALL delete the branch, print what it deleted, and create
the branch and worktree anew. Merged-ness SHALL be judged by content — an
ancestry check plus a squash-aware probe — never by `git branch --merged`
alone, and a detached root HEAD SHALL be an error under `--fresh`.

#### Scenario: Squash-merged branch is recreated fresh
- **GIVEN** branch `change/epic-close-x` whose commits were squash-merged into
  the base branch, with no worktree
- **WHEN** `worktree.sh epic-close-x --fresh` runs
- **THEN** the old branch is deleted and announced, and
  `.worktrees/epic-close-x` exists on a new `change/epic-close-x` starting at
  the base branch, exit zero

#### Scenario: Unmerged branch refuses fresh creation
- **GIVEN** branch `change/epic-close-x` carrying a commit not merged into the
  base branch
- **WHEN** `worktree.sh epic-close-x --fresh` runs
- **THEN** it exits non-zero naming the unmerged branch, and the branch and
  its commit still exist

#### Scenario: Existing worktree refuses fresh creation
- **GIVEN** `.worktrees/my-change` already exists
- **WHEN** `worktree.sh my-change --fresh` runs
- **THEN** it exits non-zero and neither the worktree nor the branch changes

### Requirement: Guarded pruning of merged change branches
id: prune-merged-change-branches

The worktree helper SHALL provide a `prune-branches` verb that, run from the
repository root, deletes every local `change/*` branch whose content is merged
into the base branch — judged by the same content-based, squash-aware probe as
the fresh-branch flag — and SHALL never delete the root checkout's current
branch, any branch checked out in a worktree, any unmerged branch, or any
branch outside `change/*`. It SHALL print one line per deleted branch and one
per kept candidate with the reason, and SHALL exit zero whether or not
anything was deleted. If the root checkout's HEAD is detached, then the verb
SHALL error exiting non-zero.

#### Scenario: Squash-merged local branches are pruned and listed
- **GIVEN** local branches `change/a` and `change/b` whose content was
  squash-merged into the base branch, with no worktrees attached
- **WHEN** `worktree.sh prune-branches` runs
- **THEN** both branches are deleted, each named on a `pruned:` line, and the
  exit code is zero

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

## MODIFIED Requirements

### Requirement: Epic derivation in the build close-out
id: epic-close-out-derivation
base: cec3bbc69eeb

When a shipped change's plan carried an `Epic:` line, the build flow's
close-out SHALL, after the PR merges and main is pulled, run `epic-sync`
for that epic from a fresh `epic-close-<slug>` worktree — never from the
main checkout — creating that worktree with the worktree helper's
fresh-branch flag (`--fresh`) so the derivation never starts from a stale
`change/epic-close-<slug>` branch, and, only when the derivation changes
the epic's status line, commit and ship the advance as an auto-merging PR;
when the status is unchanged, the worktree is removed with no PR. The
close-out SHALL NOT run the derivation pre-merge, because member archives
reach main only after the squash merge.

#### Scenario: Member merge advances the epic via a PR
- **GIVEN** a shipped change whose plan carried `Epic: reporting-overhaul`
  and whose merge archived the epic's last member
- **WHEN** the build close-out runs
- **THEN** `epic-sync` runs in an `epic-close-reporting-overhaul` worktree
  and the status advance ships as an auto-merging PR

#### Scenario: Close-out worktree is created fresh
- **GIVEN** a stale merged `change/epic-close-reporting-overhaul` branch left
  over from a previous close-out
- **WHEN** the build close-out creates its worktree
- **THEN** the helper is invoked with the fresh-branch flag, so the stale
  branch is deleted and the derivation starts from the base branch

#### Scenario: Unchanged derivation ships nothing
- **WHEN** the close-out's `epic-sync` derives the status the epic already
  carries
- **THEN** no commit or PR is created and the worktree is removed
