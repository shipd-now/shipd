## MODIFIED Requirements

### Requirement: Ship changes as auto-merging PRs
id: ship-changes-as-prs
base: 1554d4927943

When a change is verified and merged/archived on its branch, build SHALL ship
it by pushing the branch (`git push -u origin change/<name>`), opening a PR
(`gh pr create --fill`), and enabling auto-merge with squash and branch
deletion (`gh pr merge --auto --squash --delete-branch`). Build SHALL NOT
commit or push to `main` directly; a `ci` status check on the PR SHALL gate
the merge. When reporting the PR in any status update or completion report,
build SHALL give the full clickable PR URL, never just the number. If
auto-merge is unavailable, build SHALL merge manually only after `ci` is
green and SHALL say so in the report.

Arming auto-merge is not proof of merge. Immediately after arming it, build
SHALL read the PR's `mergeStateStatus` once; if it is anything other than
`CLEAN` or `UNSTABLE` (i.e. `DIRTY`, `BEHIND`, or `BLOCKED`), build SHALL
reconcile the branch by merging `origin/main` into it in the worktree and
re-pushing — re-posting the `semantic-review` gate on the new head, since a new
commit invalidates the prior status — or, when the conflict is non-trivial,
surface it as a blocker rather than leaving auto-merge waiting on a merge that
cannot happen. While a build is unattended (an autopilot-driven member), a
non-trivial conflict SHALL park the member rather than prompt a human.

Build SHALL then watch **its own** PR to a terminal state, polling `state` and
`mergeStateStatus` together on each cycle: a transition to `DIRTY`, `BEHIND`, or
`BLOCKED` SHALL be acted on within a poll cycle (reconcile or surface) exactly as
`MERGED` ends the watch. The close-out SHALL wait for this PR to reach `MERGED`
before pruning the worktree, pulling `main`, and running any epic derivation, so
a subsequent build lands on a `main` that already carries this change. Build
SHALL NOT block one change's close-out on any other PR's state.

Build SHALL NOT open a follow-up PR on a branch whose PR has already
squash-merged. A review finding that arrives after merge SHALL either have
blocked the original PR before merge or be planned as a new change against
current `main`.

#### Scenario: Verified change becomes a PR
- **WHEN** verification passes and the spec merge/archive is committed on
  `change/dark-mode-toggle`
- **THEN** the branch is pushed, a PR is opened with auto-merge (squash)
  enabled, and the completion report links the PR's full URL

#### Scenario: No direct main pushes
- **WHEN** a build finishes while `ci` has not yet passed on its PR
- **THEN** nothing is pushed to `main`; the merge happens only through the
  PR once the check is green

#### Scenario: Un-mergeable PR is reconciled, not awaited
- **GIVEN** auto-merge has just been armed and the PR's `mergeStateStatus`
  reads `DIRTY`
- **WHEN** build checks mergeability after arming
- **THEN** it merges `origin/main` into the branch and re-pushes (re-posting the
  gate on the new head), or surfaces a non-trivial conflict as a blocker —
  never leaving auto-merge to wait indefinitely

#### Scenario: A stuck watched PR is acted on, not awaited forever
- **GIVEN** build is watching its own PR and the PR transitions to `BLOCKED`
- **WHEN** the next poll cycle observes the transition
- **THEN** build reconciles or surfaces it within that cycle rather than waiting
  on a merge that cannot complete

#### Scenario: One stuck PR does not delay another close-out
- **GIVEN** two shipped changes whose PRs are watched independently, one of which
  is stuck `DIRTY`
- **WHEN** the other PR reaches `MERGED`
- **THEN** its close-out runs without waiting on the stuck PR

#### Scenario: No follow-up PR on a squash-merged branch
- **WHEN** a review finding is raised after the change's PR has squash-merged
- **THEN** it is planned as a new change against current `main`, not opened as a
  second PR on the merged branch
