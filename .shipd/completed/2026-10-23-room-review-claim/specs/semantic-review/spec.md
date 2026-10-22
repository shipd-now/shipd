## ADDED Requirements

### Requirement: The room poster checks its claim before posting
id: gate-poster-room-claim-fence

When `review_gate.py post` runs with `--room-agent` and the environment
carries `SHIPD_ROOM_CLAIM`, it SHALL check the claim immediately before its
first GitHub write and again immediately before submitting the review. The
check SHALL pass only when the claim's head is the pull request's current
head, no newer generation exists for the claimed head, no `done` ref exists
for it, the claim ref's tip names this claim's holder in state `claimed` or
`beat`, and that tip is under 300 seconds old by GitHub's clock. If the first
check fails, then `post` SHALL make no GitHub write. If the second check
fails, then `post` SHALL submit no review. Either failure SHALL print one
line starting `room claim lost` that says what was already posted, and SHALL
exit non-zero. Once the summary is posted for the claimed head and the second
check has passed, `post` SHALL create the claim's `done` ref and set
`room-review/<agent>` to `success`, whether or not a review object was
submitted. When `post` runs with `--room-agent`, `SHIPD_ROOM_CLAIM_REQUIRED=1`
and no `SHIPD_ROOM_CLAIM`, it SHALL make no GitHub write, SHALL print one
line starting `room claim lost`, and SHALL exit non-zero. Without either
variable, `post` SHALL behave as before this requirement.

#### Scenario: A turn without a claim cannot post
- **WHEN** `post --room-agent rev-b` runs with `SHIPD_ROOM_CLAIM_REQUIRED=1`
  and no `SHIPD_ROOM_CLAIM`
- **THEN** it writes nothing, prints a `room claim lost` line, and exits
  non-zero

#### Scenario: A moved head stops the post
- **WHEN** the claim names head `abc` and the pull request's head is now
  `def`
- **THEN** `post` writes nothing and prints a `room claim lost` line

#### Scenario: A comment-only post still finishes the claim
- **WHEN** the acting login authored the pull request and no finding anchors,
  so no review object is submitted
- **THEN** `post` still creates the `done` ref and sets `room-review/<agent>`
  to `success`

#### Scenario: A newer generation stops the post
- **WHEN** the claim names generation `1` and generation `2` exists for the
  head
- **THEN** `post` writes no summary, no review and no status, prints a
  `room claim lost` line, and exits non-zero

#### Scenario: An old heartbeat stops the post
- **WHEN** the claim tip is 301 seconds older than GitHub's current time
- **THEN** `post` writes nothing and prints a `room claim lost` line

#### Scenario: A fresh claim posts and is marked done
- **WHEN** the claim is the newest and its tip is 20 seconds old
- **THEN** `post` submits the review, creates the `done` ref, and sets
  `room-review/<agent>` to `success`

#### Scenario: No claim keeps today's behaviour
- **WHEN** `post --room-agent rev-b` runs without `SHIPD_ROOM_CLAIM`
- **THEN** it makes no claim call and posts exactly as before
