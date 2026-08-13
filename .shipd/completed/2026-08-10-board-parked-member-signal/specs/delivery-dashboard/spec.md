## ADDED Requirements

### Requirement: Board parked-member signal
id: board-parked-member-signal

The board SHALL surface a **parked** member — one the delivery pipeline could
not carry forward — with an at-a-glance signal on its lane card and, in its
spec-detail modal, an obvious rendering of the validation output that parked it,
so a parked member is never mistaken for an idle or an actively-driving one. The
signal SHALL be derived by a **pure, dependency-free predicate** over the
member's worktree-derived board state and its heartbeat roster entry (no
`textual`, no I/O), unit-testable without the TUI.

A member is parked when its roster entry was marked **stale** by dead-run
detection, or when its roster entry state (or, absent an entry, its
worktree-derived board state) is `rejected` or `needs-human`. For each parked
kind the predicate SHALL yield a distinct **error-tier glyph** and a short
**state label**: a stale card yields `†` with `stale (<death age>)` reusing the
death age dead-run detection already writes onto the entry; a `rejected` member
yields `⚠` with `rejected`; a `needs-human` member yields `⛔` with
`needs-human`. It SHALL also carry the entry's `reason` when present. A member
progressing normally — driving, ready, unplanned, or shipped — SHALL yield no
signal.

On the **lane card**, a parked member SHALL render its signal glyph in the
theme's error color in place of the risk glyph, followed by the slug and the
state label in the muted tier. The shipped `✓` card and the actively-driving
`● slug · <stage>` card SHALL be unchanged, and the parked signal SHALL fold
into the diff-aware refresh so a member entering or leaving a parked state
repaints its lane.

In the **spec-detail modal** badge meta row, a parked member SHALL render an
error-tier **state chip** carrying the state label in place of the muted
live-stage chip; the live-stage chip SHALL appear only while the member is being
driven, never for a parked member whose stage is a stale leftover. When the
parked member's roster entry carries a `reason`, the modal SHALL present it as a
**tinted callout above the artifact tabs**: the theme's error color at 10% alpha
for the background, a solid error-colored one-cell bar along the callout's full
left edge, and the reason text in the theme's warning tier — the member-level
analogue of the epic stall banner — so the validation output is obvious without
opening the Plan tab. A parked member with no recorded reason SHALL render the
state chip but no callout, and a non-parked member's modal SHALL render neither
the state chip nor the callout. All new chrome SHALL reference colors only
through `$` theme variables.

#### Scenario: A rejected member's card carries the warning glyph and state label
- **GIVEN** a member whose worktree-derived board state is `rejected`
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `⚠` glyph, the slug, and `· rejected` in
  the muted tier — not the risk glyph

#### Scenario: A needs-human member's card carries the stop glyph
- **GIVEN** a member whose roster entry state is `needs-human`
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `⛔` glyph, the slug, and `· needs-human`
  in the muted tier

#### Scenario: A stale dead-run card carries the dagger glyph and death age
- **GIVEN** a driving member marked stale by dead-run detection, its entry
  carrying the `died <age>` death age
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `†` glyph, the slug, and
  `· stale (died <age>)` — not an actively-driving `● slug · <stage>` card

#### Scenario: A normal card is unchanged
- **GIVEN** a ready member (or a driving member, or a shipped member)
- **WHEN** its lane card text renders
- **THEN** it renders the existing risk glyph (or the driving stage suffix, or
  the shipped `✓`) with no parked-signal glyph or state label

#### Scenario: The parked-signal predicate is pure and dependency-free
- **GIVEN** a member dict and a roster entry, evaluated with `textual` not
  importable
- **WHEN** the parked-signal predicate is called
- **THEN** it returns the kind, glyph, label, and reason for a parked member and
  `None` for a normally-progressing one, raising no error

#### Scenario: A parked member's modal shows a state chip, not a stale stage chip
- **GIVEN** a `rejected` member whose roster entry still carries a leftover
  `stage: gate`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows an error-tier `rejected` state chip and renders
  no `stage:` chip

#### Scenario: A parked member's modal surfaces the reason in the tinted callout
- **GIVEN** a `rejected` member whose roster entry carries a `reason`
- **WHEN** its spec-detail modal opens
- **THEN** a callout above the artifact tabs renders the reason text on the
  theme's error color at 10% alpha with a solid error-colored one-cell bar on
  its left edge

#### Scenario: A driving member's modal keeps its live-stage chip
- **GIVEN** a member being driven at stage `build`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows the muted `stage: build` chip and renders no
  state chip and no reason callout

#### Scenario: A parked member with no reason shows the chip but no callout
- **GIVEN** a `needs-human` member whose roster entry carries no `reason`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows the error-tier `needs-human` state chip and no
  reason callout is mounted

#### Scenario: A parked flip repaints the lane
- **GIVEN** a rendered board whose member flips from `driving` to `rejected`
- **WHEN** the diff-aware refresh compares lane signatures
- **THEN** the signatures differ and the affected lane repaints
