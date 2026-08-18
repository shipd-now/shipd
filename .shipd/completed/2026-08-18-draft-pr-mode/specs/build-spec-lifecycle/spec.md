## MODIFIED Requirements

### Requirement: Ship changes as auto-merging PRs
id: ship-changes-as-prs
base: 1a8372157912

When a change is verified and merged/archived on its branch, build SHALL ship
it by pushing the branch (`git push -u origin change/<name>`), opening a PR
(`gh pr create --fill`), and enabling auto-merge with squash and branch
deletion (`gh pr merge --auto --squash --delete-branch`). Build SHALL NOT
commit or push to `main` directly; a `ci` status check on the PR SHALL gate
the merge. When reporting the PR in any status update or completion report,
build SHALL give the full clickable PR URL, never just the number. If
auto-merge is unavailable, build SHALL merge manually only after `ci` is
green and SHALL say so in the report.

Where the resolved configuration declares `pr-mode: draft` (shipd-config
pr-mode-key), build SHALL instead open the PR as a draft
(`gh pr create --fill --draft`) and SHALL NOT enable auto-merge. The
gate-posting obligations below apply unchanged in draft mode — build SHALL
still post the semantic-review gate with the review entry's declared options
and run its disposition loop, honoring the skipped-review carve-out — but the
merge watch and the merged close-out (worktree pruning, `main` pull, epic
derivation) SHALL NOT run: the ship's terminal state is the open draft PR,
and build SHALL end by reporting its full URL and that merging is now a
human's step, leaving the worktree and branch in place. Draft mode governs
change-shipping PRs only; metadata PRs (epic-close status derivations,
initiative tagging) SHALL keep auto-merging regardless of the mode. If the
resolved `pr-mode` value is neither `auto` nor `draft`, then build SHALL stop
before pushing and report the error naming `pr-mode`.

Arming auto-merge is not proof of merge. Immediately after arming it, build
SHALL read the PR's `mergeStateStatus` once. `CLEAN` or `UNSTABLE`, and a
`BLOCKED` state on a branch that is neither `BEHIND` nor `DIRTY` (merely
awaiting required checks — in this repo, the `semantic-review` gate not yet
posted or `ci` still running), are on track: build SHALL post the gate and let
the checks run, NOT merge `origin/main`. When posting the gate, build SHALL
pass the resolved pipeline's review entry's declared `disposition` and
`model` through to the `/s:review` post flow and follow that flow's
matching scoped disposition loop; an entry declaring neither leaves the
posting unchanged. Where the resolved pipeline explicitly skips or omits
the `review` stage, build SHALL NOT post the gate, and the PR watch SHALL
surface a PR still blocked on a required check as a blocker. Only a `DIRTY`
or `BEHIND` state (or a
`BLOCKED` caused by a behind/conflicting branch) means the PR cannot merge as
armed; there build SHALL reconcile the branch by merging `origin/main` into it
in the worktree and re-pushing — re-posting the `semantic-review` gate on the
new head, since a new commit invalidates the prior status — or, when the
conflict is non-trivial, surface it as a blocker rather than leaving auto-merge
waiting on a merge that cannot happen. While a build is unattended (an
autopilot-driven member), a non-trivial conflict SHALL park the member rather
than prompt a human.

Under `auto` mode, build SHALL then watch **its own** PR to a terminal state,
polling `state` and
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

#### Scenario: Draft mode opens a draft PR without auto-merge
- **GIVEN** a workspace config layer declaring `"pr-mode": "draft"`
- **WHEN** build ships a verified change from a member repo
- **THEN** the PR is created with `--draft`, no auto-merge is armed, the
  semantic-review gate is still posted per the review entry, no merge watch
  or close-out runs, and the report gives the draft PR's full URL as the
  terminal state with the worktree left in place

#### Scenario: Metadata PRs ignore draft mode
- **GIVEN** `pr-mode: draft` resolved
- **WHEN** an epic-close derivation ships its status edit as a PR
- **THEN** that PR is opened auto-merging exactly as before

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

#### Scenario: Review entry options reach the gate posting
- **GIVEN** a resolved review entry declaring `disposition` `high-only`
  and `model` `tier-below`
- **WHEN** build posts the semantic-review gate for its PR
- **THEN** the `/s:review` post flow is invoked with
  `disposition=high-only` and `model=tier-below` and its `high-only`
  disposition loop runs

#### Scenario: Skipped review posts no gate
- **GIVEN** a declared pipeline carrying `{"stage": "review", "skip":
  true}`
- **WHEN** build ships the change's PR
- **THEN** no semantic-review gate is posted, and a PR blocked on a
  still-required check is surfaced by the watch as a blocker
