# build-spec-lifecycle — delta

## ADDED Requirements

### Requirement: One change per worktree and branch
id: change-worktree-isolation

Every change SHALL be developed in its own git worktree at
`.worktrees/<change>` on a branch named `change/<change>`, created via
`scripts/worktree.sh <change>`, and the entire lifecycle — planning artifacts,
implementation, verification, and the spec merge/archive — SHALL run inside
that worktree so the change's artifacts, code, and applied specs travel in a
single PR. The main checkout SHALL be used only for launching sessions,
reviewing, post-merge pulls, and the plugin snapshot refresh.

#### Scenario: Lifecycle stays in the worktree
- **WHEN** a build executes a change named `dark-mode-toggle`
- **THEN** all edits, the task checklist churn, and the `spec_merge.py`
  archive happen under `.worktrees/dark-mode-toggle` on branch
  `change/dark-mode-toggle`, and the main checkout's working tree is
  untouched

#### Scenario: Parallel sessions do not collide
- **WHEN** two sessions build two different changes concurrently
- **THEN** each works in its own worktree and branch, and neither session's
  uncommitted state appears in the other's commits

### Requirement: Ship changes as auto-merging PRs
id: ship-changes-as-prs

When a change is verified and merged/archived on its branch, build SHALL ship
it by pushing the branch (`git push -u origin change/<name>`), opening a PR
(`gh pr create --fill`), and enabling auto-merge with squash and branch
deletion (`gh pr merge --auto --squash --delete-branch`). Build SHALL NOT
commit or push to `main` directly; a `ci` status check on the PR SHALL gate
the merge. When reporting the PR in any status update or completion report,
build SHALL give the full clickable PR URL, never just the number. If
auto-merge is unavailable, build SHALL merge manually only after `ci` is
green and SHALL say so in the report.

#### Scenario: Verified change becomes a PR
- **WHEN** verification passes and the spec merge/archive is committed on
  `change/dark-mode-toggle`
- **THEN** the branch is pushed, a PR is opened with auto-merge (squash)
  enabled, and the completion report links the PR's full URL

#### Scenario: No direct main pushes
- **WHEN** a build finishes while `ci` has not yet passed on its PR
- **THEN** nothing is pushed to `main`; the merge happens only through the
  PR once the check is green
