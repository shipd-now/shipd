## ADDED Requirements

### Requirement: Board drafted-member state
id: board-drafted-member

While a member's heartbeat roster entry records the terminal state `drafted`
— an autopilot member whose draft-mode pipeline ended with an open draft PR
(epic-autopilot pipeline-stage-execution) — the board SHALL treat it as
awaiting human review and merge, never as shipped. The run heartbeat SHALL
record the `drafted` outcome as roster state `drafted` through an explicit
entry in its outcome-to-state mapping, not an unmapped fall-through. The
lane mapping SHALL place a member whose roster entry state is `drafted` in
the `review` lane, and SHALL check that roster state before the
archived-to-shipped branch: a drafted member's worktree-derived board state
reads `archived` (its change is archived while its PR stays open), and that
state SHALL NOT carry it into the `shipped` lane.

The member-signal predicate SHALL yield, for a member whose roster entry
state (or, absent an entry, worktree-derived board state) is `drafted`, an
informational signal `{"kind": "drafted", "glyph": "◇", "label": "drafted"}`
carrying the entry's `reason` when present — remaining pure and
dependency-free exactly like the parked kinds. The lane card SHALL render
the `◇` glyph in an accent/informational tier — never the theme's error
color — followed by the slug and the `drafted` state label in the muted
tier. Parked-member semantics are unchanged: a drafted member is not
parked, and the spec-detail modal renders it as a normal member (terminal
outcomes already clear the leftover `stage` from the roster entry).

#### Scenario: A drafted member lands in the review lane, not shipped
- **GIVEN** a member whose roster entry state is `drafted` and whose
  worktree-derived board state is `archived`
- **WHEN** its lane is computed
- **THEN** the member is placed in the `review` lane, not `shipped`

#### Scenario: A drafted card carries the info glyph and state label
- **GIVEN** a member whose roster entry state is `drafted`
- **WHEN** its lane card text renders
- **THEN** the text is the `◇` glyph in an accent tier (not the error
  color), the slug, and `· drafted` in the muted tier

#### Scenario: The roster maps the drafted outcome first-class
- **WHEN** the run heartbeat records a member finishing with outcome
  `drafted`
- **THEN** the roster entry's state is `drafted` via an explicit mapping
  entry, and its `stage` is cleared like any terminal outcome

#### Scenario: The drafted signal is pure and dependency-free
- **GIVEN** a member dict with a `drafted` roster entry, evaluated with
  `textual` not importable
- **WHEN** the member-signal predicate is called
- **THEN** it returns kind `drafted`, glyph `◇`, and label `drafted`,
  raising no error
