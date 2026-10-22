## ADDED Requirements

### Requirement: One review per head through an atomic claim
id: room-review-claim

Before a `reviewer` or `ci` turn, in repo mode and PR mode alike, `room run`
SHALL claim the pull request's head by creating
`refs/shipd/claims/pr-<N>/<agent>/<sha>/<gen>` through the GitHub API, and
SHALL run the turn only when its create succeeded. A run SHALL create
generation `1` when no claim exists, and the next generation only when the
newest claim is marked `released` or its last claim commit is more than 600
seconds old, measured as GitHub's `Date` header minus the commit's
`committer.date`. While its turn runs, the winner SHALL move its claim ref to
a new claim commit every 60 seconds. A run that finds a live claim held by
another holder SHALL skip the turn without advancing its cursor. A run that
finds the newest claim marked `done` SHALL skip the turn and advance its
cursor. After the turn, a claim the poster did not mark `done` SHALL be
marked `released`. The `CLAIM_ENV` variable SHALL carry the won claim to the
session for the turn only.

#### Scenario: Two runners race for one head
- **WHEN** two runners of `rev-b` try to claim head `abc` of PR 7 and the
  fake GitHub answers the second create with `422 Reference already exists`
- **THEN** exactly one runner calls its turn runner, and the other writes a
  `claimed by` line and calls none

#### Scenario: A stale claim is taken over by a new generation
- **WHEN** generation `1` for head `abc` was last stamped 601 seconds before
  GitHub's current time and is not `done`
- **THEN** the run creates generation `2` and calls its turn runner

#### Scenario: A live claim is left alone
- **WHEN** generation `1` for head `abc` was stamped 30 seconds ago by
  another holder
- **THEN** the run creates nothing, calls no turn runner, and leaves its
  cursor where it was

#### Scenario: A done claim counts as reviewed
- **WHEN** the newest claim for head `abc` is marked `done`
- **THEN** the run calls no turn runner and advances its cursor past the
  task

#### Scenario: A turn that posts nothing releases the claim
- **WHEN** the turn runner returns and the claim tip is not marked `done`
- **THEN** the run writes a `released` claim commit, so another runner can
  claim the head at once

### Requirement: A reviewer without push permission refuses to start
id: room-review-claim-permission

A `room run` with role `reviewer` or `ci` SHALL read `permissions.push` of
the repository before joining any room. If it is not true, then the run SHALL
print one `Error:` line naming the acting login and the repository and saying
that review claims need push permission, SHALL post nothing, SHALL call no
runner, and SHALL exit `1`.

#### Scenario: No push permission
- **WHEN** `repos/o/r` answers `permissions.push: false` and
  `room run --repo o/r --role reviewer --agent rev-b` starts
- **THEN** stderr holds one `Error:` line naming the login and `o/r`, no room
  is joined, and the exit code is `1`

#### Scenario: Authors need no claim permission
- **WHEN** `repos/o/r` answers `permissions.push: false` and an `author` run
  starts on PR 7
- **THEN** the run is not refused for permission

### Requirement: A claimed review holds a merge-guard status
id: room-review-status

When a run wins a claim, it SHALL set the commit status
`room-review/<agent>` on the claimed head to `pending`. When the poster
submits the claimed review, the status SHALL become `success`. When the claim
is released, the status SHALL stay `pending`. A repository makes merges wait
for the claimed review by listing `room-review/<agent>` in
`merge.required_checks`.

#### Scenario: Won claim sets pending
- **WHEN** a run of `rev-b` wins the claim on head `abc`
- **THEN** the fake GitHub records a `pending` status with context
  `room-review/rev-b` on `abc`

### Requirement: Closed pull requests lose their claims
id: room-review-claim-cleanup

When a run sees a pull request close (repo mode: it leaves the open listing;
PR mode: the room reports it closed), the run SHALL delete every ref under
`refs/shipd/claims/pr-<N>/`. A failed delete SHALL print one `warning:` line
and SHALL NOT stop the run.

#### Scenario: Repo mode deletes a closed PR's claims
- **WHEN** PR 7 had claim refs and drops out of the open listing
- **THEN** the fake GitHub receives a delete for each ref under
  `refs/shipd/claims/pr-7/`
