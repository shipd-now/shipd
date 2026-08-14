## ADDED Requirements

### Requirement: Board stall signal
id: board-stall-signal

The board SHALL treat an epic as **stalled** when its live heartbeat's run
`state` is `finished` and at least one roster entry sits at `state:
"needs-human"`; `rejected` entries SHALL NOT stall an epic. The stall predicate
and the accessor for the stalled entries SHALL be pure, dependency-free
functions over the aggregated epic dict (no `textual`, no I/O). While an epic
is stalled, its group header title SHALL carry a `✗` marker rendered in the
registered theme's error color immediately before the epic's slug, and the
stall state SHALL fold into the diff-aware refresh so a stall appearing or
clearing repaints the affected lanes. The stalled epic's **epic-detail modal**
SHALL present a warning block naming each `needs-human` member with its parked
stage and reason, plus a **Retry** control; activating Retry SHALL dispatch the
same detached epic-level autopilot run the group header's run control
dispatches and dismiss the modal. A non-stalled epic's modal SHALL render
neither the warning nor the Retry control.

#### Scenario: Stalled epic is marked in its group header
- **GIVEN** an epic whose heartbeat run is `finished` with a `needs-human`
  roster entry
- **WHEN** its group header renders
- **THEN** the title carries the theme-error-colored `✗` marker before the slug

#### Scenario: Rejected members do not stall
- **GIVEN** an epic whose finished heartbeat roster holds `rejected` and
  `shipped` entries but no `needs-human` entry
- **WHEN** the stall predicate evaluates it
- **THEN** the epic is not stalled and its header renders no marker

#### Scenario: Stalled epic's modal warns and offers Retry
- **GIVEN** a stalled epic
- **WHEN** its epic-detail modal opens
- **THEN** a warning block lists each `needs-human` member with its stage and
  reason, and a Retry control is present

#### Scenario: Retry dispatches the epic-level run
- **GIVEN** a stalled epic's open epic-detail modal
- **WHEN** the user activates Retry
- **THEN** the detached epic-level autopilot launch is dispatched and the modal
  is dismissed

#### Scenario: A stall flip repaints the lane
- **GIVEN** a rendered board whose epic then flips between `needs-human` and
  `driving` roster states with an unchanged stage
- **WHEN** the diff-aware refresh compares lane signatures
- **THEN** the signatures differ and the affected lane repaints
