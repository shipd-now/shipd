## MODIFIED Requirements

### Requirement: Board epic grouping
id: board-epic-grouping
base: 82d15617f951

The `tui` board SHALL provide a three-state **grouping mode** — `epic`, `initiative`, `none` — selected from a **segmented control in the header bar** (one compact one-row button per mode, the active mode visibly highlighted) and cycled in that order by the footer-bound `g` key, and SHALL start in **`epic`** mode by default. While the mode is `epic`, every lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
header** (one group per epic, in board order, each group individually
collapsible), replacing the previous shipped-lane-only grouping — so an epic's
cards in a lane sit together under that epic's header. Each epic group header
SHALL show the epic's slug and status and, when the epic belongs to an
initiative, that **initiative** (its slug), and the **count of that epic's
cards in that lane**; this re-homes the initiative → epic
structure that the removed hierarchy panel used to carry. The group's visual
SHALL be a flat **theme surface band** (the registered theme's panel
background) with **theme-variable border separator lines** dividing adjacent
groups — no per-epic-status colour coding and no hard-coded colors (see the
Board theme requirement). The group header SHALL be a **single terminal row**
— no top-border row above the title and no trailing padding row below the
group's contents, so the title row (collapse arrow, title text, and the
controls) is the group's first row. Each **runnable** epic group
header SHALL carry a **clickable run control**; an epic is **runnable** when its
status is `ready` or `active` **and** it has at least one `unplanned` or `ready`
member (there is something for the autopilot to drive). A **non-runnable** epic —
a `complete`/`archived` epic, or one with no drivable members — SHALL NOT render a
run control at all, so a closed epic can never be run from the board. Activating a
run control SHALL NOT toggle the group's collapsed state (the two affordances are
distinct); instead it SHALL open a **confirmation modal** reading exactly "This
will deliver the full epic, are you sure you want to continue?" with a **Yes**
control and a **No** control, plus a **close (✕) control in its top-left**. The
**epic-level run** (the same autopilot launch the removed hierarchy panel
triggered) SHALL be dispatched **only** when the user chooses **Yes**; choosing
**No**, the ✕ control, or `Escape` SHALL dismiss the modal **without** dispatching
any run. Independently of the run control, **every** epic group header SHALL also
carry a **clickable open control** — distinct from both the run control and the
collapse toggle, and present on every epic whether runnable or not — that opens an
**epic-detail modal** for that epic. The header's title row SHALL lay its
children out in **normal flex flow with reserved widths — never as
positioned overlays**: the title (collapse arrow plus title text) fills the
remaining width and, when too wide, SHALL truncate with an **ellipsis inside
its own space**; the controls follow as ordinary trailing children — the run
control first (when present), then the open control — inside the group's
panel. The **per-lane card count** SHALL render inside the title as a
trailing ` (N)` suffix in the **muted foreground colour**, not as a separate
trailing element. A header control SHALL never overlap the
title, never be painted over clipped text, and never render
outside its group row, whatever the title length. The header controls and every modal **close (✕) control**
SHALL be **compact — a single row high and exactly three cells wide** — while
remaining visually evident as clickable buttons. The **epic-detail modal** SHALL
occupy the
majority of the viewport, carry a **close (✕) control** the user can click (in
addition to `Escape`), and present the epic's slug and status, its theme and
initiative when set, a **list of the epic's member specs** — each showing its board
state and risk and **clickable to open that change's own spec-detail modal**
(the same spec-detail modal a lane card opens, pushed on top of the epic-detail
modal so dismissing it returns to the epic-detail modal) — and the epic's own
overview rendered as **Markdown** from its
`epics/<slug>/epic.md` artifact. Reading that epic artifact SHALL be a
**dependency-free** operation (no `textual`), so it is unit-tested without the
TUI. Activating the open control SHALL NOT toggle the group's collapsed state, and
dismissing the epic-detail modal (its ✕ control or `Escape`) SHALL return to the
board. While the mode is `initiative`, every lane SHALL render its cards grouped under a **collapsible per-initiative header** — one group per initiative in the aggregation's group order, titled with the initiative's slug and status, the epics carrying no `Initiative:` collected under a single `workspace` group — fed by the aggregation's existing initiative `groups`; an initiative header carries **no run and no open control** (both are epic-scoped). While the mode is `none`, every lane SHALL render its cards **flat** — no group headers — matching the pre-grouping lane layout. The grouping mode SHALL fold into the diff-aware refresh so an idle board never repaints and a collapsed group stays collapsed across refreshes; any mode change SHALL repaint the lanes.
Removing the hierarchy panel SHALL NOT change the board's **data layer**
(`build_board`, the aggregation, the epic-run launch builder): only the rendering
and the run trigger move.

#### Scenario: Epic mode is the default
- **WHEN** the app is mounted with no override
- **THEN** the grouping mode is `epic` and each lane's cards render under
  per-epic headers

#### Scenario: Each lane groups its cards under per-epic headers when grouped
- **GIVEN** the grouping mode is `epic` and a lane holds cards from two different epics
- **WHEN** the lane is rendered
- **THEN** the cards appear under two collapsible epic headers, each header
  naming its epic, with each epic's cards beneath its own header

#### Scenario: An epic group header shows the epic's initiative
- **GIVEN** the grouping mode is `epic` and an epic that belongs to an initiative
- **WHEN** that epic's group header renders
- **THEN** the header shows the epic's slug and status and the initiative it
  belongs to

#### Scenario: The header shows the epic's per-lane card count
- **GIVEN** the grouping mode is `epic` and an epic with two cards in one lane
- **WHEN** that epic's group header renders in that lane
- **THEN** the header's title ends with a ` (2)` suffix rendered in the muted
  foreground colour, and no separate count element follows the controls

#### Scenario: The group header is a single row
- **GIVEN** the grouping mode is `epic`
- **WHEN** an epic group renders
- **THEN** its title row is the group's topmost row — no border row above it —
  and the run/open controls sit on that same row

#### Scenario: Epic groups use a theme surface band with theme border separators
- **GIVEN** the grouping mode is `epic`
- **WHEN** a lane's epic groups render
- **THEN** each group has the theme's panel background and adjacent groups are
  divided by a theme border-variable separator line, with no per-epic-status
  colour applied

#### Scenario: A runnable epic shows a run control
- **GIVEN** the grouping mode is `epic` and an epic whose status is `ready` or `active` with
  at least one `unplanned` or `ready` member
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable run control

#### Scenario: The header controls flow at the end of the title row
- **GIVEN** the grouping mode is `epic` and a runnable epic's group header
- **WHEN** the header renders
- **THEN** the run control and then the open control sit as flex children on
  the title row after the title's space, inside the group's panel, each one
  row high and three cells wide, and neither overlaps the title text

#### Scenario: Modal close controls are one row high
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal is
  open
- **WHEN** its close (✕) control renders
- **THEN** that control occupies a single row, three cells wide

#### Scenario: A non-runnable epic's header carries only the open control
- **GIVEN** the grouping mode is `epic` and a non-runnable epic's group header
- **WHEN** the header renders
- **THEN** the open control follows the title's space with no run control
  before it

#### Scenario: An overlong title ellipsizes beside the controls
- **GIVEN** the grouping mode is `epic` and an epic whose rendered header title is wider
  than its lane
- **WHEN** the header renders
- **THEN** the title truncates with an ellipsis inside its own space while the
  run/open controls render fully inside the lane, not overlapping any text,
  and remain clickable

#### Scenario: A non-runnable epic shows no run control
- **GIVEN** the grouping mode is `epic` and a `complete`/`archived` epic (or one with no
  `unplanned`/`ready` member)
- **WHEN** that epic's group header renders
- **THEN** the header carries no run control, so the epic cannot be run from the
  board

#### Scenario: Clicking a run control opens the confirmation modal
- **GIVEN** the grouping mode is `epic` and a runnable epic's run control
- **WHEN** the run control is clicked
- **THEN** a confirmation modal reading "This will deliver the full epic, are you
  sure you want to continue?" is pushed onto the screen stack, no epic-level run
  has been dispatched yet, and the group's collapsed state is unchanged

#### Scenario: Confirming with Yes dispatches the epic-level run
- **GIVEN** an open epic-run confirmation modal for an epic
- **WHEN** the user activates its Yes control
- **THEN** the epic-level run is dispatched for that epic and the modal is
  dismissed

#### Scenario: Declining or closing the modal runs nothing
- **GIVEN** an open epic-run confirmation modal
- **WHEN** the user activates its No control, its ✕ close control, or presses
  `Escape`
- **THEN** the modal is dismissed and no epic-level run is dispatched

#### Scenario: Every epic group header carries an open control
- **GIVEN** the grouping mode is `epic` and any epic (runnable or not)
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable open control distinct from the run
  control

#### Scenario: Clicking the open control opens the epic-detail modal
- **GIVEN** the grouping mode is `epic` and an epic group header's open control
- **WHEN** the open control is clicked
- **THEN** an epic-detail modal for that epic is pushed onto the screen stack and
  the group's collapsed state is unchanged

#### Scenario: The epic-detail modal lists the epic's member specs
- **GIVEN** an epic with member specs
- **WHEN** its epic-detail modal opens
- **THEN** the modal shows the epic's slug and status and a list of its member
  specs, each with its board state and risk

#### Scenario: Clicking a member spec opens its spec-detail modal
- **GIVEN** an open epic-detail modal listing the epic's member specs
- **WHEN** the user clicks one of the listed member specs
- **THEN** that change's spec-detail modal is pushed onto the screen stack (the
  same modal a lane card opens), on top of the epic-detail modal, and dismissing
  it returns to the epic-detail modal

#### Scenario: The epic-detail modal shows the epic overview
- **GIVEN** an epic whose `epics/<slug>/epic.md` artifact exists
- **WHEN** its epic-detail modal opens
- **THEN** the modal renders that epic artifact's content as Markdown

#### Scenario: The epic-detail modal is dismissed by its close control
- **GIVEN** an open epic-detail modal
- **WHEN** the user clicks its ✕ close control or presses `Escape`
- **THEN** the modal is dismissed and the board screen is shown again

#### Scenario: Reading the epic artifact is dependency-free
- **GIVEN** an environment without `textual`
- **WHEN** the epic-artifact helper is called for an epic that has an
  `epics/<slug>/epic.md`
- **THEN** it returns that epic's Markdown text without importing `textual`

#### Scenario: Selecting none renders flat lanes
- **GIVEN** the grouping mode is `epic`
- **WHEN** the mode is set to `none` (via the segmented control or by
  cycling `g`)
- **THEN** every lane re-renders its cards flat, with no group headers

#### Scenario: A collapsed epic group hides its cards
- **GIVEN** the grouping mode is `epic` and an epic group whose header is expanded
- **WHEN** that group's header is collapsed
- **THEN** that epic's cards in the lane are hidden while another epic's group
  stays visible

#### Scenario: The g key cycles the grouping mode
- **GIVEN** the mounted board in `epic` mode
- **WHEN** `g` is pressed three times
- **THEN** the mode advances through `initiative` and `none` back to `epic`,
  the segmented control highlights the active mode at each step, and the lanes
  repaint at each step

#### Scenario: A mode button selects its mode directly
- **GIVEN** the mounted board in `epic` mode
- **WHEN** the segmented control's `initiative` button is activated
- **THEN** the grouping mode becomes `initiative` and the active highlight
  moves to that button

#### Scenario: Initiative mode groups lanes by initiative
- **GIVEN** the grouping mode is `initiative`, two epics sharing one
  initiative, and one epic carrying none
- **WHEN** a lane holding cards from all three epics renders
- **THEN** the shared-initiative epics' cards sit under one collapsible header
  titled with the initiative's slug and status, the third epic's cards sit
  under a `workspace` group header, and no initiative header carries a run or
  open control

## ADDED Requirements

### Requirement: Lane row presentation
id: lane-row-presentation

The board's lane rows SHALL present as follows: header controls (the run and
open controls) SHALL use a neutral surface background while idle, taking an
accent-tinted background only on hover and on focus; each group's panel band
SHALL extend unbroken to its divider, with no lane-background gap between
the group's last card and the divider; and every lane card (and the epic
modal's member rows) SHALL render its text on a single line, truncating an
overlong slug with an ellipsis — never wrapping onto a cropped second line
that leaves the slug invisible. The test suite SHALL carry a board-screen
chrome sweep, run at two terminal widths, asserting every group header's
buttons sit inside their lane's scrollable content region and every card's
painted line begins with its slug's visible prefix.

#### Scenario: Idle controls are neutral, hover and focus accent
- **WHEN** an epic group header renders without the pointer over its
  controls
- **THEN** the run/open controls carry the neutral surface background, and
  hovering or focusing a control gives it the accent-tinted background

#### Scenario: The group band reaches the divider
- **GIVEN** an epic group with cards in a lane
- **WHEN** the group renders
- **THEN** the panel background covers the full group box down to the
  divider, with no lane-background gap after the last card

#### Scenario: A long slug ellipsizes instead of blanking
- **GIVEN** a lane whose width leaves a card one cell narrower than its
  `✓ <slug>` text
- **WHEN** the card renders
- **THEN** its single painted line shows the slug's prefix with an ellipsis,
  not a bare glyph with the slug invisible

#### Scenario: The board sweep guards lane rows at multiple widths
- **WHEN** the board-screen chrome sweep runs at two different terminal
  widths
- **THEN** it asserts header buttons are inside their lane's scrollable
  content region and card lines begin with their slug prefix, failing on
  any violation
