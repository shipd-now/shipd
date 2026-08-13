# group-action-menu
Status: verified

## Idea

Replace each epic group header's two floating controls with a single `≡`
menu control inside the ticket band that opens a compact Run/View action
menu, and pin the header bar's grouping segments so they never move when the
active mode changes.

### Motivation

The separate ▶ and ≡ read as detached, oddly indented floaters right of the
ticket band — the user wants one hamburger inside the band opening a popup
with Run and View options; separately, selecting a grouping mode makes the
`none` segment jump because the active segment's styling changes the
segmented control's layout.

### Details

- Every epic group header carries exactly one `≡` menu control as the title
  row's last child inside the panel band; activating it opens a compact
  action menu offering **View epic** (always) and **Run epic** (only when
  the epic is runnable). View pushes the epic-detail modal; Run pushes the
  existing run-confirmation modal (dispatch still only on Yes); Escape/✕
  dismisses without acting. The separate run control is gone.
- The three grouping segments (epic/initiative/none) keep fixed positions
  and widths across active-mode changes.

Affected capabilities: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to runnable gating, the confirmation prompt, the epic-level
  dispatch, or the epic-detail modal's content.
- No card-level action changes (`r`/`l`/`o` keys unchanged).
- No new keyboard binding for the menu (click-driven, like the controls it
  replaces).

## Implementation

- **Menu control.** `_mount_epic_groups._flush` mounts one `≡` Button
  (`classes="epic-menu-button compact-button"`, carrying `epic_menu_slug`)
  as the row's last child; the run button and `epic_open_slug` wiring are
  deleted. The row stays `[Collapsible (1fr)][≡]`, so the control sits flush
  inside the band with no gap. `epic_is_runnable` keeps gating — now the
  menu's Run item instead of a second button.
- **Action menu screen.** New `EpicActionMenuScreen(ModalScreen)` styled
  like `EpicRunConfirmScreen` (small centred box, accent title bar naming
  the epic, ✕ close): a `View epic` Button always, a `Run epic…` Button only
  when the epic was runnable at open. Handlers: View → dismiss then
  `push_screen(EpicDetailScreen(slug))`; Run → dismiss then
  `push_screen(EpicRunConfirmScreen(slug))`; ✕/`escape` dismiss without
  acting. `BoardApp.on_button_pressed` routes `epic_menu_slug` buttons to
  push the menu (replacing the two old routes, whose marker attributes go
  away).
- **Segment stability.** The jump comes from state-dependent layout on the
  `width: auto` mode buttons when `mode-active` toggles (`text-style: bold`
  plus textual's Button state styles). Fix by giving each `.mode-button` a
  fixed width equal to its label plus padding (`epic`→6, `initiative`→12,
  `none`→6 — set `width` per-id or via `auto` replaced with explicit
  widths) and dropping `text-style: bold` from `.mode-active` if it still
  reflows; the test asserts identical regions across all three active
  states, which pins whichever mechanism remained.
- **Test migration.** Header-control tests move to the menu contract
  (presence, in-band placement, menu open/dismiss, View/Run routing,
  runnable gating of the Run item); the board sweep's button-containment
  assertions apply to the menu control unchanged.
- **Risk**: double-push timing (dismiss then push) must land the pushed
  screen on the board, not on the dismissed menu — the handlers push from
  the app after `dismiss()`, mirroring how `EpicRunConfirmScreen.Yes`
  already dispatches post-dismiss.
