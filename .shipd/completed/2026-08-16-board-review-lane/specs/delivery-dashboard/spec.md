## ADDED Requirements

### Requirement: Board live-build lane
id: board-live-build-lane

While a member's attached interactive build heartbeat is live — state
`running` with a liveness stamp (the newer of its `updated_at` and the
aggregation-stamped transcript mtime) within the 600-second build-freshness
window — the board's lane resolution SHALL place the member's card in the
`review` lane while the heartbeat's stage is `review`, and in the `building`
lane at any other stage, overriding the member's lifecycle-state mapping (so
an already-archived member whose interactive build is mid-review renders in
`review`, not `shipped`). A live autopilot roster entry in state `driving`
SHALL keep precedence over the build heartbeat, so autopilot-driven placement
is unchanged. If the build heartbeat is not live — state `finished`, or its
liveness stamp aged past the window — then lane resolution SHALL fall back to
the existing state mapping unchanged, with no stale treatment (the dagger
signal remains autopilot-roster-only). While a card is placed by a live build
heartbeat, its row SHALL append the heartbeat's stage in the muted tier after
the slug, the same rendering as a roster-driven member, and the member's
spec-detail modal SHALL show the muted `stage:` chip derived from that
heartbeat whenever no roster stage chip or parked signal applies.

#### Scenario: An archived member mid-review renders in the review lane
- **GIVEN** a member whose board state is `archived` with an attached build
  heartbeat of state `running`, stage `review`, and a fresh `updated_at`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `review` lane and the `shipped` lane
  does not carry it

#### Scenario: A non-review build stage renders in building
- **GIVEN** a member with a live build heartbeat at stage `implement`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `building` lane

#### Scenario: A stale build heartbeat falls back to the state mapping
- **GIVEN** an `archived` member whose build heartbeat records state `running`
  at stage `review` but a liveness stamp older than the freshness window
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `shipped` lane

#### Scenario: A driving roster entry keeps precedence
- **GIVEN** a member whose live autopilot roster entry is `driving` at stage
  `build` and whose build heartbeat is live at stage `review`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `building` lane, per the roster entry

#### Scenario: The card row appends the live build stage
- **GIVEN** a member card placed by a live build heartbeat at stage `review`
- **WHEN** the card's row text renders
- **THEN** the stage is appended in the muted tier after the slug

#### Scenario: The modal shows the build-stage chip
- **GIVEN** the spec-detail modal of a member with a live build heartbeat at
  stage `review` and no roster stage or parked signal
- **WHEN** the modal's badge row composes
- **THEN** it carries the muted `stage: review` chip and its lane badge reads
  `review`
