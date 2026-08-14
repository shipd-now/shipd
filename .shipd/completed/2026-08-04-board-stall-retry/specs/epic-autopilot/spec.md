## ADDED Requirements

### Requirement: Stale worktree reclaim
id: stale-worktree-reclaim

If a member's worktree creation fails and the failure output contains `already
exists`, then the autopilot SHALL attempt a reclaim before parking: remove the
leftover worktree through the guarded `worktree.sh remove` verb invoked with
the activity guard disabled (`SHIPD_WORKTREE_IDLE_MINUTES=0`) and every other
guard in force, delete the leftover `change/<slug>` branch with a merged-only
delete (`git branch -d`), and retry the creation exactly once. If the guarded
remove refuses or the merged-only branch delete fails, the autopilot SHALL
park the member `needs_human` at the `worktree` stage with that command's
output as the reason and SHALL NOT force the removal. A creation failure whose
output does not contain `already exists` SHALL park the member exactly as
before, with no reclaim attempt. Every reclaim command SHALL run through the
autopilot's command seam so the sequence is testable without git.

#### Scenario: Clean leftover is reclaimed and the drive proceeds
- **GIVEN** worktree creation fails with `already exists` and the guarded
  remove, branch delete, and retried creation all succeed
- **WHEN** the autopilot drives the member
- **THEN** the member proceeds into its stage pipeline instead of parking

#### Scenario: Guard refusal parks with the refusal as reason
- **GIVEN** worktree creation fails with `already exists` and the guarded
  remove exits non-zero (e.g. a dirty tree)
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` at the `worktree` stage with the
  refusal output as its reason, and no forced removal occurs

#### Scenario: Unmerged branch parks instead of losing work
- **GIVEN** the guarded remove succeeds but `git branch -d` fails because the
  branch is not fully merged
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` with the delete failure as its
  reason and the branch is left in place

#### Scenario: Other creation failures park unchanged
- **GIVEN** worktree creation fails with output not containing `already exists`
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` at the `worktree` stage as before and
  no reclaim command runs
