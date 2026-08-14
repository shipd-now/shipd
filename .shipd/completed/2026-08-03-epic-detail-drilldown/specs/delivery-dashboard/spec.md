## MODIFIED Requirements

### Requirement: Board epic grouping
id: board-epic-grouping
base: e155bafca106

The `tui` board SHALL provide a **group-by-epic** mode, toggled from a control in
the **controls strip** above the lanes and also from a footer-bound key, and
SHALL start with grouping **on** by default. When grouping is **on**, every
lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
header** (one group per epic, in board order, each group individually
collapsible), replacing the previous shipped-lane-only grouping — so an epic's
cards in a lane sit together under that epic's header. Each epic group header
SHALL show the epic's slug and status and, when the epic belongs to an
initiative, that **initiative** (its slug); this re-homes the initiative → epic
structure that the removed hierarchy panel used to carry. The group's visual
SHALL be a plain **gray background** with **black separator lines** dividing
adjacent groups — no per-epic-status colour coding. Each **runnable** epic group
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
**epic-detail modal** for that epic. The **epic-detail modal** SHALL occupy the
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
board. When grouping is **off**, every lane SHALL render its cards **flat** — no
epic headers — matching the pre-grouping lane layout. Grouping state SHALL fold
into the diff-aware refresh so an idle board never repaints and a collapsed group
stays collapsed across refreshes; toggling the mode SHALL repaint the lanes.
Removing the hierarchy panel SHALL NOT change the board's **data layer**
(`build_board`, the aggregation, the epic-run launch builder): only the rendering
and the run trigger move.

#### Scenario: Grouping is on by default
- **WHEN** the app is mounted with no override
- **THEN** the group-by-epic mode is active and each lane's cards render under
  per-epic headers

#### Scenario: Each lane groups its cards under per-epic headers when grouped
- **GIVEN** grouping is on and a lane holds cards from two different epics
- **WHEN** the lane is rendered
- **THEN** the cards appear under two collapsible epic headers, each header
  naming its epic, with each epic's cards beneath its own header

#### Scenario: An epic group header shows the epic's initiative
- **GIVEN** grouping is on and an epic that belongs to an initiative
- **WHEN** that epic's group header renders
- **THEN** the header shows the epic's slug and status and the initiative it
  belongs to

#### Scenario: Epic groups use a gray background with black separators
- **GIVEN** grouping is on
- **WHEN** a lane's epic groups render
- **THEN** each group has a gray background and adjacent groups are divided by a
  black separator line, with no per-epic-status colour applied

#### Scenario: A runnable epic shows a run control
- **GIVEN** grouping is on and an epic whose status is `ready` or `active` with
  at least one `unplanned` or `ready` member
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable run control

#### Scenario: A non-runnable epic shows no run control
- **GIVEN** grouping is on and a `complete`/`archived` epic (or one with no
  `unplanned`/`ready` member)
- **WHEN** that epic's group header renders
- **THEN** the header carries no run control, so the epic cannot be run from the
  board

#### Scenario: Clicking a run control opens the confirmation modal
- **GIVEN** grouping is on and a runnable epic's run control
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
- **GIVEN** grouping is on and any epic (runnable or not)
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable open control distinct from the run
  control

#### Scenario: Clicking the open control opens the epic-detail modal
- **GIVEN** grouping is on and an epic group header's open control
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

#### Scenario: Toggling grouping off renders flat lanes
- **GIVEN** grouping is on
- **WHEN** the group-by-epic toggle is switched off
- **THEN** every lane re-renders its cards flat, with no epic headers

#### Scenario: A collapsed epic group hides its cards
- **GIVEN** grouping is on and an epic group whose header is expanded
- **WHEN** that group's header is collapsed
- **THEN** that epic's cards in the lane are hidden while another epic's group
  stays visible
