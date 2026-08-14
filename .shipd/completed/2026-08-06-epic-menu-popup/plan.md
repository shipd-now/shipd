# epic-menu-popup
Status: verified

## Idea

Turn the epic action menu from a centred, board-dimming modal dialog into a
small popup anchored to its `≡` control that does not dim the board and
dismisses on click-away — matching a header-style dropdown menu.

### Motivation

The action menu currently opens as a centred modal box with an accent title
bar and a ✕, dimming the whole board — the user wants it to behave like a
header menu: a small list popup pinned near the `≡` control, non-modal (no
dim), dismissed by clicking elsewhere or pressing Escape.

### Details

- The action menu opens anchored just below its `≡` control (clamped to stay
  on screen), presents its actions as a compact keyboard-navigable list with
  no title bar and no ✕, leaves the board undimmed behind it, and dismisses
  without acting on Escape or a click outside the menu box.
- The action items, runnable gating, and routing are unchanged: View epic
  always, Run epic only when runnable; View opens the epic-detail modal, Run
  opens the run-confirmation modal (dispatch still only on Yes).

Affected capabilities: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to which items appear, their gating, or the modals they route to.
- No change to the `≡` control's placement or the confirmation flow.
- No change to any other modal (spec-detail, epic-detail, run-confirm keep
  their centred, dimming, titled chrome).

## Implementation

- **Anchor coordinates.** `BoardApp.on_button_pressed` reads the pressed
  `≡` button's `region` and passes its screen `(x, y)` to
  `_push_epic_menu(slug, anchor)`; the menu screen stores the anchor and, on
  mount, sets its box `offset` to open just below-left of the control,
  clamped to the screen size so a control near the right/bottom edge opens
  inward rather than off-screen (a small pure `menu_offset(anchor, box_size,
  screen_size)` helper, unit-tested).
- **Non-dimming screen.** `EpicActionMenuScreen` keeps being a `ModalScreen`
  (the robust way to capture an outside click) but its screen background
  becomes **transparent** — no dim — and its box is `offset`-positioned
  rather than `align: center middle`. Rejected: a mounted overlay widget on
  the board screen — click-outside dismissal then needs a full-screen catch
  widget anyway, i.e. the same mechanism with more plumbing.
- **List presentation.** The box drops the accent title bar and the ✕; its
  body is a single `OptionList` (added to the widget imports) with `View
  epic` and, when runnable, `Run epic…`. `↑`/`↓` move the highlight, `Enter`
  or click selects, mirroring the screenshot's highlighted-row look.
  Selection dismisses with `"view"`/`"run"`; the board callback is unchanged.
- **Click-away + Escape dismiss.** `Escape` dismisses with `None` (unchanged
  binding). A `Click` on the screen outside the menu box dismisses with
  `None` — the standard textual context-menu pattern (the box stops its own
  clicks; a click that reaches the screen is outside it).
- **Routing unchanged.** `_push_epic_menu`'s `_after` callback still pushes
  `EpicDetailScreen`/`EpicRunConfirmScreen` post-dismiss, so the chosen
  modal lands on the board.
- **Risk**: the offset clamp must keep the whole box on screen for a control
  in the rightmost lane (the common case) — covered by the `menu_offset`
  unit tests at edge anchors and by a headless open-at-shipped-lane test.
