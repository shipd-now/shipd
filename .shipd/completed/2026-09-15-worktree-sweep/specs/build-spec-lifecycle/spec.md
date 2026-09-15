## ADDED Requirements

### Requirement: Opportunistic worktree sweep
id: worktree-sweep-verb

The worktree helper SHALL provide a `sweep [--dry-run]` verb that, run from the
repository root, reclaims the worktrees under `.worktrees/` whose work has
already shipped and then runs the `prune-branches` verb's branch reclamation.

For each `.worktrees/<name>`, the verb SHALL resolve the worktree's checked-out
branch and SHALL skip it — reporting nothing — while that branch carries no
commits ahead of the resolved base branch, so a freshly created or otherwise
untouched worktree is never a sweep candidate. Where the branch is ahead of the
base, the verb SHALL judge merged-ness by the same two probes `prune-branches`
consults, in the same order: the content-based, squash-aware probe, and — where
that reports not-merged — whether the branch's remote-tracking ref is absent.

Where the branch is merged, the verb SHALL evaluate the `remove` verb's guard
chain and SHALL remove the worktree only when no guard fires, reporting it on a
`swept:` line; where any guard fires, the verb SHALL leave the worktree in place
and report it on a `kept:` line naming every guard reason. The verb SHALL NOT
force a removal past a guard under any circumstances.

Where the branch is not merged, the verb SHALL NOT remove the worktree under any
condition. While that worktree's branch tip is older than the resolved stale
window, the verb SHALL report it on a `stale:` line naming the worktree and the
age of its branch tip; otherwise it SHALL report it on a `kept:` line.

The verb SHALL exit zero whether or not anything was removed, so a caller's own
outcome never depends on housekeeping. If the root checkout's HEAD is detached,
then the verb SHALL report that no base branch resolves, skip both the worktree
pass and the branch prune, and still exit zero. Where `--dry-run` is given, the
verb SHALL print exactly the report it would otherwise print and SHALL remove no
worktree and delete no branch.

#### Scenario: A merged clean worktree is swept
- **GIVEN** `.worktrees/shipped` on a branch one commit ahead of the base whose
  content was squash-merged into it, with a clean tree, nothing under
  `.shipd/planned/`, and no claims
- **WHEN** `worktree.sh sweep` runs
- **THEN** the worktree is gone, it is named on a `swept:` line, and the exit
  code is zero

#### Scenario: A freshly created worktree is never swept
- **GIVEN** `.worktrees/new-change` created moments ago, whose branch carries no
  commits ahead of the base
- **WHEN** `worktree.sh sweep` runs
- **THEN** the worktree still exists and no line names it

#### Scenario: A merged worktree with live work is kept
- **GIVEN** `.worktrees/shipped` whose branch is merged and ahead of the base,
  carrying an unshipped change under `.shipd/planned/` and a `[~]` claim
- **WHEN** `worktree.sh sweep` runs
- **THEN** the worktree still exists, a `kept:` line names it with both guard
  reasons, and the exit code is zero

#### Scenario: An abandoned unmerged worktree is reported, never removed
- **GIVEN** `.worktrees/abandoned` with a clean tree, no planned change, and a
  branch one commit ahead of the base that is not merged and whose tip is older
  than the stale window
- **WHEN** `worktree.sh sweep` runs
- **THEN** the worktree still exists and a `stale:` line names it with the age
  of its branch tip

#### Scenario: A recent unmerged worktree is kept quietly
- **GIVEN** the same worktree with a branch tip inside the stale window
- **WHEN** `worktree.sh sweep` runs
- **THEN** the worktree still exists, a `kept:` line names it, and no `stale:`
  line is printed

#### Scenario: Merged branches are pruned in the same run
- **GIVEN** a local `change/gone` whose content merged into the base and which
  is checked out in no worktree
- **WHEN** `worktree.sh sweep` runs
- **THEN** the branch is deleted and named on a `pruned:` line

#### Scenario: Dry run changes nothing
- **GIVEN** a repository holding both a sweepable worktree and a prunable branch
- **WHEN** `worktree.sh sweep --dry-run` runs
- **THEN** both the `swept:` and `pruned:` lines are printed, the worktree still
  exists, the branch still exists, and the exit code is zero

#### Scenario: A detached root HEAD still exits zero
- **GIVEN** a repository whose root checkout has a detached HEAD
- **WHEN** `worktree.sh sweep` runs
- **THEN** no worktree is removed, no branch is deleted, the output reports that
  no base branch resolves, and the exit code is zero

## MODIFIED Requirements

### Requirement: Guarded pruning of merged change branches
id: prune-merged-change-branches
base: f46ddb75e8d1

The worktree helper SHALL provide a `prune-branches [--dry-run]` verb that, run
from the repository root, deletes every local `change/*` branch whose content is
merged into the base branch and SHALL never delete the root checkout's current
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
anything was deleted. Where `--dry-run` is given, the verb SHALL print exactly
the report it would otherwise print and SHALL delete no branch. If the root
checkout's HEAD is detached, then the verb SHALL error exiting non-zero.

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

#### Scenario: Dry run deletes no branch
- **GIVEN** a local `change/a` whose content was squash-merged into the base
- **WHEN** `worktree.sh prune-branches --dry-run` runs
- **THEN** the `pruned:` line naming `change/a` is printed, the branch still
  exists, and the exit code is zero
