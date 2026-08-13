## MODIFIED Requirements

### Requirement: Board epic grouping
id: board-epic-grouping
base: ae1b24a91612

The `tui` board SHALL provide a three-state **grouping mode** — `epic`, `initiative`, `none` — selected from a **segmented control in the header bar** (one compact one-row button per mode, the active mode visibly highlighted) and cycled in that order by the footer-bound `g` key, and SHALL start in **`epic`** mode by default. The three mode segments SHALL keep **fixed positions and widths** regardless of which mode is active — selecting a mode never moves any segment. While the mode is `epic`, every lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
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
group's contents, so the title row (collapse arrow, title text, and the menu
control) is the group's first row. Every epic group header SHALL carry
exactly one **menu control (`≡`)** rendered **inside the group's panel band
as the title row's last child** — no other header control. Activating the
menu control SHALL NOT toggle the group's collapsed state; it SHALL open a
compact **action menu** for that epic offering **View epic** always and
**Run epic** only when the epic is **runnable** — an epic is runnable when
its status is `ready` or `active` **and** it has at least one `unplanned` or
`ready` member (there is something for the autopilot to drive), so a
`complete`/`archived` epic (or one with no drivable member) can never be run
from the board. Choosing **View epic** SHALL dismiss the menu and open the
**epic-detail modal**; choosing **Run epic** SHALL dismiss the menu and open
a **confirmation modal** reading exactly "This
will deliver the full epic, are you sure you want to continue?" with a **Yes**
control and a **No** control, plus a **close (✕) control in its top-left**. The
**epic-level run** (the same autopilot launch the removed hierarchy panel
triggered) SHALL be dispatched **only** when the user chooses **Yes**; choosing
**No**, the ✕ control, or `Escape` SHALL dismiss the confirmation **without** dispatching
any run; and the action menu itself SHALL dismiss without acting on
`Escape` or its own ✕ control. The header's title row SHALL lay its
children out in **normal flex flow with reserved widths — never as
positioned overlays**: the title (collapse arrow plus title text) fills the
remaining width and, when too wide, SHALL truncate with an **ellipsis inside
its own space**; the menu control follows as the row's ordinary trailing
child inside the group's panel. The **per-lane card count** SHALL render inside the title as a
trailing ` (N)` suffix in the **muted foreground colour**, not as a separate
trailing element. The menu control SHALL never overlap the
title, never be painted over clipped text, and never render
outside its group row, whatever the title length. The header menu control and every modal **close (✕) control**
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
TUI. Dismissing the epic-detail modal (its ✕ control or `Escape`) SHALL return to the
board. While the mode is `initiative`, every lane SHALL render its cards grouped under a **collapsible per-initiative header** — one group per initiative in the aggregation's group order, titled with the initiative's slug and status, the epics carrying no `Initiative:` collected under a single `workspace` group — fed by the aggregation's existing initiative `groups`; an initiative header carries **no menu control** (epic actions are epic-scoped). While the mode is `none`, every lane SHALL render its cards **flat** — no group headers — matching the pre-grouping lane layout. The grouping mode SHALL fold into the diff-aware refresh so an idle board never repaints and a collapsed group stays collapsed across refreshes; any mode change SHALL repaint the lanes.
Removing the hierarchy panel SHALL NOT change the board's **data layer**
(`build_board`, the aggregation, the epic-run launch builder): only the rendering
and the run trigger move.

#### Scenario: Epic mode is the default
- **WHEN** the app is mounted with no override
- **THEN** the grouping mode is `epic` and each lane's cards render under
  per-epic headers

#### Scenario: Mode segments never move
- **GIVEN** the mounted board in `epic` mode
- **WHEN** each of the three modes is selected in turn
- **THEN** every segment button's region is identical across all three
  states

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
  foreground colour, and no separate count element follows the menu control

#### Scenario: The group header is a single row
- **GIVEN** the grouping mode is `epic`
- **WHEN** an epic group renders
- **THEN** its title row is the group's topmost row — no border row above it —
  and the menu control sits on that same row

#### Scenario: Epic groups use a theme surface band with theme border separators
- **GIVEN** the grouping mode is `epic`
- **WHEN** a lane's epic groups render
- **THEN** each group has the theme's panel background and adjacent groups are
  divided by a theme border-variable separator line, with no per-epic-status
  colour applied

#### Scenario: The menu control sits inside the band at the title row's end
- **GIVEN** the grouping mode is `epic` and any epic's group header
- **WHEN** the header renders
- **THEN** the `≡` menu control is the title row's last child inside the
  group's panel band, one row high and three cells wide, not overlapping the
  title, with no other header control present

#### Scenario: Modal close controls are one row high
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal is
  open
- **WHEN** its close (✕) control renders
- **THEN** that control occupies a single row, three cells wide

#### Scenario: An overlong title ellipsizes beside the menu control
- **GIVEN** the grouping mode is `epic` and an epic whose rendered header title is wider
  than its lane
- **WHEN** the header renders
- **THEN** the title truncates with an ellipsis inside its own space while the
  menu control renders fully inside the lane, not overlapping any text, and
  remains clickable

#### Scenario: A runnable epic's menu offers Run and View
- **GIVEN** the grouping mode is `epic` and a runnable epic
- **WHEN** its menu control is activated
- **THEN** a compact action menu opens naming the epic, offering View epic
  and Run epic, and the group's collapsed state is unchanged

#### Scenario: A non-runnable epic's menu offers only View
- **GIVEN** the grouping mode is `epic` and a `complete`/`archived` epic (or one with no
  `unplanned`/`ready` member)
- **WHEN** its menu control is activated
- **THEN** the action menu offers View epic and no Run item, so the epic
  cannot be run from the board

#### Scenario: Choosing Run epic opens the confirmation modal
- **GIVEN** a runnable epic's open action menu
- **WHEN** the user chooses Run epic
- **THEN** the menu is dismissed and the confirmation modal reading "This
  will deliver the full epic, are you sure you want to continue?" is pushed,
  with no epic-level run dispatched yet

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

#### Scenario: The action menu dismisses without acting
- **GIVEN** an open action menu
- **WHEN** the user presses `Escape` or clicks its ✕ control
- **THEN** the menu closes, no run is dispatched, and no modal is pushed

#### Scenario: Choosing View epic opens the epic-detail modal
- **GIVEN** any epic's open action menu
- **WHEN** the user chooses View epic
- **THEN** the menu is dismissed and an epic-detail modal for that epic is
  pushed onto the screen stack, with the group's collapsed state unchanged

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
  under a `workspace` group header, and no initiative header carries a menu
  control
