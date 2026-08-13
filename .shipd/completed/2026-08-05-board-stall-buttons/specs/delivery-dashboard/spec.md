## MODIFIED Requirements

### Requirement: Board stall signal
id: board-stall-signal
base: 8c72a325e467

The board SHALL treat an epic as **stalled** when its live heartbeat's run
`state` is `finished` and at least one roster entry sits at `state:
"needs-human"`; `rejected` entries SHALL NOT stall an epic. The stall predicate
and the accessor for the stalled entries SHALL be pure, dependency-free
functions over the aggregated epic dict (no `textual`, no I/O). While an epic
is stalled, its group header title SHALL carry a `✗` marker rendered in the
registered theme's error color immediately before the epic's slug, and the
stall state SHALL fold into the diff-aware refresh so a stall appearing or
clearing repaints the affected lanes.

The stalled epic's **epic-detail modal** SHALL present the stall banner as a
tinted panel: the theme's error color at reduced (10%) alpha for the
background, with a solid error-colored bar one cell wide along the banner's
full left edge, and content in the theme's normal foreground tiers — never a
solid error background with white text. The banner SHALL carry, top to
bottom: a header row with a bold error-colored `STALLED` label and a
right-aligned muted summary naming the parked count (`N member(s) parked ·
needs-human`); one row per `needs-human` member showing its slug in the
default foreground, its parked stage in the muted tier, and its reason as a
warning-colored chip on a warning-tinted (10%) background; a muted
reassurance line stating retry is safe because every step is checkpointed and
the run resumes from the last durable state; and an action row pairing a
**Retry** control whose visible label reads exactly `Retry run` (never
truncated), styled as a primary control (solid accent background, dark bold
label), with a right-aligned subtle `parked <age> ago` label derived from the
heartbeat's `updated_at`. Activating Retry SHALL dispatch the same detached
epic-level autopilot run the group header's run control dispatches and
dismiss the modal. A non-stalled epic's modal SHALL render neither the banner
nor the Retry control.

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

#### Scenario: Stalled epic's modal warns in the tinted accent-bar banner
- **GIVEN** a stalled epic
- **WHEN** its epic-detail modal opens
- **THEN** a panel with the theme's error color at 10% alpha as background and
  a solid error-colored one-cell bar on its left edge shows the bold
  error-colored `STALLED` header with the right-aligned muted parked summary,
  each `needs-human` member's slug with its muted stage and warning-chip
  reason, the muted retry-safety reassurance line, and an action row with a
  primary control labeled exactly `Retry run` beside a right-aligned
  `parked <age> ago` label

#### Scenario: Retry dispatches the epic-level run
- **GIVEN** a stalled epic's open epic-detail modal
- **WHEN** the user activates the `Retry run` control
- **THEN** the detached epic-level autopilot launch is dispatched and the modal
  is dismissed

#### Scenario: A stall flip repaints the lane
- **GIVEN** a rendered board whose epic then flips between `needs-human` and
  `driving` roster states with an unchanged stage
- **WHEN** the diff-aware refresh compares lane signatures
- **THEN** the signatures differ and the affected lane repaints

## ADDED Requirements

### Requirement: Board control hierarchy
id: board-control-hierarchy

The `tui` board SHALL style its action controls in a two-tier hierarchy
expressed only through registered theme variables: **primary** action
controls (the stall banner's `Retry run`, the epic-run confirmation's `Yes`)
SHALL render a solid accent background with dark bold label text, and
**secondary** controls (the confirmation's `No`) SHALL render the
hover-background elevation with muted label text. The grouping segmented
control SHALL render its active mode as a solid accent block with dark bold
text and its inactive modes on the hover-background elevation with muted
text. Where a modal's accent title bar carries its inline `✕` close control,
the control SHALL render its dark glyph directly on the accent background
rather than as an accent-tinted chip.

#### Scenario: Confirm controls split into primary and secondary
- **WHEN** the epic-run confirmation modal renders
- **THEN** its `Yes` control resolves the solid accent background with dark
  bold label text and its `No` control resolves the hover background with
  muted text

#### Scenario: Active grouping mode is a solid accent block
- **WHEN** the segmented grouping control renders with a mode active
- **THEN** the active mode's button resolves the solid accent background with
  dark bold text while the inactive mode buttons resolve the hover background
  with muted text

#### Scenario: Title-bar close matches the accent bar
- **WHEN** a modal's accent title bar renders its inline `✕` close control
- **THEN** the control's background resolves to the accent color and its
  glyph color to the theme's dark background
