## ADDED Requirements

### Requirement: Board modal chrome
id: board-modal-chrome

The board's three modals — the spec-detail, epic-detail, and epic-run
confirmation screens — SHALL each carry a one-row **accent title bar**: a band
in the theme's accent color spanning the modal's top, naming the modal's
subject (the member's slug, the epic's slug, or the epic run being confirmed)
in a contrasting foreground, with the compact `✕` close control inline at the
bar's right edge (unchanged in size and behavior). Below the title bar the
spec-detail modal SHALL show a **badge meta row** of theme-tinted chips — a
risk chip colored through the theme's risk variables, a lane chip colored
through the member's lane variable, while the member is being driven a
live-stage chip in the muted tier, and the epic reference — and the
epic-detail modal SHALL show a status chip plus theme and initiative chips
when set. The epic-detail modal's member rows SHALL each carry a **lane
badge** colored through the theme variable of that member's lane, derived by
the same lane derivation the board's lanes use. The spec-detail modal's
artifact **tab strip** SHALL be themed through theme variables — the active
tab in the accent, inactive tabs in the muted tier — and every modal SHALL
carry a one-row muted **footer key-hint line** at its bottom naming that
modal's keys. While a detail modal is open, `y` SHALL copy the modal's
subject slug via the app clipboard, and `j`/`k` SHALL scroll the modal's
content pane down/up; in the spec-detail modal `Tab` SHALL activate the next
artifact tab, wrapping past the last. When `o` is pressed in a detail modal,
the app SHALL open that modal's artifact — the spec-detail modal's active tab
file, the epic-detail modal's `epics/<slug>/epic.md` — in the user's editor
as a **suspend launch** built by a pure builder returning `{"mode":
"suspend", "argv": [<editor>, <path>], "cwd": <the file's directory>}`, with
the editor resolved from `$EDITOR` and falling back to `vi`. If the modal has
no such artifact on disk, then `o` SHALL be a no-op. All new modal chrome
SHALL reference colors only through `$` theme variables (see the Board theme
requirement).

#### Scenario: Modals carry an accent title bar with inline close
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** its top row is an accent-background title bar naming the modal's
  subject, with the compact `✕` close control inline at the bar's right edge

#### Scenario: The spec-detail modal shows a badge meta row
- **GIVEN** a member with a risk rating being driven through a stage
- **WHEN** its spec-detail modal opens
- **THEN** a badge row below the title bar shows a risk chip colored by the
  member's risk, a lane chip colored by the member's lane, a muted live-stage
  chip, and the epic reference

#### Scenario: The epic-detail modal shows status, theme, and initiative chips
- **GIVEN** an epic with a theme and an initiative
- **WHEN** its epic-detail modal opens
- **THEN** a badge row below the title bar shows the epic's status chip and
  chips naming its theme and initiative

#### Scenario: Epic member rows carry lane badges
- **GIVEN** an open epic-detail modal listing the epic's member specs
- **WHEN** the member rows render
- **THEN** each row carries a badge colored through the theme variable of the
  lane the board's own lane derivation assigns that member

#### Scenario: The artifact tab strip is accent-themed
- **WHEN** the spec-detail modal's artifact tabs render
- **THEN** the active tab is styled with the accent and inactive tabs with the
  muted tier, with every color a `$` theme variable

#### Scenario: Each modal shows its footer key hints
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** a one-row muted key-hint line at the modal's bottom names that
  modal's keys

#### Scenario: y copies the modal's subject slug
- **GIVEN** an open spec-detail modal (or epic-detail modal)
- **WHEN** `y` is pressed
- **THEN** the member's slug (or the epic's slug) is copied via the app
  clipboard

#### Scenario: Tab cycles the artifact tabs
- **GIVEN** an open spec-detail modal with more than one artifact tab
- **WHEN** `Tab` is pressed repeatedly
- **THEN** the active tab advances through the artifact tabs, wrapping from
  the last back to the first

#### Scenario: j and k scroll the modal content
- **GIVEN** an open detail modal whose content overflows its pane
- **WHEN** `j` then `k` is pressed
- **THEN** the content pane scrolls down then back up

#### Scenario: o opens the active artifact in the editor
- **GIVEN** an open spec-detail modal showing artifact tabs
- **WHEN** `o` is pressed
- **THEN** a suspend launch is spawned whose argv is the resolved editor
  followed by the active tab's file path

#### Scenario: o without an artifact is a no-op
- **GIVEN** an open spec-detail modal showing the not-yet-planned notice
- **WHEN** `o` is pressed
- **THEN** no launch is spawned and the modal stays open

#### Scenario: The editor launch builder is pure and falls back to vi
- **GIVEN** an environment where `$EDITOR` is unset
- **WHEN** the editor launch builder is called with an artifact path
- **THEN** it returns `{"mode": "suspend", "argv": ["vi", <path>], "cwd":
  <the file's directory>}` without spawning anything, and with `$EDITOR` set
  it uses that editor instead

## MODIFIED Requirements

### Requirement: Board epic grouping
id: board-epic-grouping
base: 10f9b69d1dc1

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
inline controls) is the group's first row. Each **runnable** epic group
header SHALL carry a **clickable run control**; an epic is **runnable** when its
status is `ready` or `active` **and** it has at least one `unplanned` or `ready`
member (there is something for the autopilot to drive). A **non-runnable** epic —
a `complete`/`archived` epic, or one with no drivable members — SHALL NOT render a
run control at all, so a closed epic can never be run from the board. Activating a
run control SHALL NOT toggle the group's collapsed state (the two affordances are
distinct); instead it SHALL open a **confirmation modal** reading exactly "This
will deliver the full epic, are you sure you want to continue?" with a **Yes**
control and a **No** control, plus its accent title bar's **inline close (✕) control**
(see the Board modal chrome requirement). The
**epic-level run** (the same autopilot launch the removed hierarchy panel
triggered) SHALL be dispatched **only** when the user chooses **Yes**; choosing
**No**, the ✕ control, or `Escape` SHALL dismiss the modal **without** dispatching
any run. Independently of the run control, **every** epic group header SHALL also
carry a **clickable open control** — distinct from both the run control and the
collapse toggle, and present on every epic whether runnable or not — that opens an
**epic-detail modal** for that epic. The header's controls SHALL render **inline
on the header's title row, immediately after the epic's title text** — the run
control first (when present), then the open control **one cell after it** (the
open control sits flush to the title when no run control renders), inside the
group's panel — never docked at the far edge of the lane row outside the
group's visual box. If the rendered title is too wide for its lane, the
controls SHALL pin inside the lane's right edge — painting over the clipped
title tail — so they stay visible and clickable; a header control SHALL never
render outside its group row. The header controls and every modal **close (✕) control**
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
- **THEN** the header's title carries the count 2 alongside the slug, status,
  and initiative

#### Scenario: The group header is a single row
- **GIVEN** the grouping mode is `epic`
- **WHEN** an epic group renders
- **THEN** its title row is the group's topmost row — no border row above it —
  and the inline run/open controls sit on that same row

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

#### Scenario: The header controls sit inline next to the epic name
- **GIVEN** the grouping mode is `epic` and a runnable epic's group header
- **WHEN** the header renders
- **THEN** the run control occupies the header's title row immediately after
  the title text with the open control one cell after it, inside the
  group's panel, not at the lane row's far edge, and each control is one row
  high and three cells wide

#### Scenario: Modal close controls are one row high
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal is
  open
- **WHEN** its close (✕) control renders
- **THEN** that control occupies a single row, three cells wide

#### Scenario: A non-runnable epic's open control sits flush to the title
- **GIVEN** the grouping mode is `epic` and a non-runnable epic's group header
- **WHEN** the header renders
- **THEN** the open control occupies the header's title row immediately after
  the title text, with no run control before it

#### Scenario: An overlong title pins the controls inside the lane
- **GIVEN** the grouping mode is `epic` and an epic whose rendered header title is wider
  than its lane
- **WHEN** the header renders
- **THEN** the run and open controls render fully inside the lane on the title
  row, pinned at the lane's right edge over the clipped title, and remain
  clickable

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
