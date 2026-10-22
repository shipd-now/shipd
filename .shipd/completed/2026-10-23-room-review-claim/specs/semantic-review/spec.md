## ADDED Requirements

### Requirement: The room poster checks its claim before posting
id: gate-poster-room-claim-fence

When `review_gate.py post` runs with `--room-agent` and the environment
carries `SHIPD_ROOM_CLAIM`, it SHALL check the claim immediately before its
first GitHub write and again immediately before submitting the review. The
check SHALL pass only when no newer generation exists for the claimed head,
the claim ref's tip names this claim's holder in state `claimed` or `beat`,
and that tip is under 300 seconds old by GitHub's clock. If the check fails,
then `post` SHALL make no further GitHub write, SHALL print one line starting
`room claim lost`, and SHALL exit non-zero. After the review is submitted,
`post` SHALL mark the claim `done` and set `room-review/<agent>` to
`success`. Without `SHIPD_ROOM_CLAIM`, `post` SHALL behave as before this
requirement.

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
- **THEN** `post` submits the review, writes a `done` claim commit, and sets
  `room-review/<agent>` to `success`

#### Scenario: No claim keeps today's behaviour
- **WHEN** `post --room-agent rev-b` runs without `SHIPD_ROOM_CLAIM`
- **THEN** it makes no claim call and posts exactly as before
