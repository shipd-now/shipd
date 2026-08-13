# card-click-detail
Status: verified

## Idea

Make a task-card on the delivery board open its detail dialog on a **mouse
click**, matching what `Enter` already does — so pointer users get to the member
detail modal the same way keyboard users do.

### Motivation

The board already has a `MemberDetailScreen` modal and opens it from a focused
`TaskCard` via the `Enter` binding (`action_select` → `push_screen`). But
`TaskCard` has no mouse handling at all, so clicking a card only focuses it (via
`can_focus`) and never opens the dialog. A pointer user clicks a ticket, nothing
happens, and the detail view is effectively keyboard-only.

### Details

- Add a `Click` event handler to `TaskCard` that focuses the clicked card and
  then opens the existing `MemberDetailScreen` for that card's member — reusing
  `action_select` so the click and `Enter` paths are identical.
- No new modal, no new content, no data-layer change: the dialog, its fields,
  and the `Enter` binding are all unchanged.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (the `TaskCard` class), a test in
`plugins/s/skills/build/tests_textual/`; plugin version bump.

### Non-goals

- No change to the modal's contents or layout, the `Enter`/`Escape` bindings, the
  `r`/`l`/`o` action keys, focus movement, or the hierarchy tree.
- No click-to-open on hierarchy-tree nodes or lane headers — this change is
  task-cards only.
- No double-click / right-click semantics — a single primary click opens the
  dialog.

## Implementation

- **Reuse `action_select`, do not duplicate the push.** `TaskCard.action_select`
  already builds and pushes `MemberDetailScreen(self.epic_slug, self.member,
  self.entry)`. The click handler SHALL call the same path so the two entry
  points can never diverge.
- **Handler shape.** In `textual`, a widget receives a mouse click as the
  `textual.events.Click` message; handle it with an `on_click(self, event)`
  method on `TaskCard`. Focus the card first (`self.focus()`) so the clicked card
  becomes the focused/highlighted one, then call `self.action_select()`. Import
  `textual.events` (or the `Click` type) alongside the other guarded `textual`
  imports at the top of `dashboard.py`, under the same import-guard that lets the
  module load without `textual`.
- **Focus semantics.** A `TaskCard` is `can_focus = True`, so textual already
  moves focus to it on click; calling `self.focus()` explicitly in the handler
  makes the "click focuses then opens" contract deterministic under the test
  harness regardless of textual's default click-focus timing. The
  `Focused card is highlighted` scenario continues to hold.
- **Test seam.** `textual`'s `Pilot` can synthesize a click with
  `await pilot.click(TaskCard)` (or a card selector). The test mounts the app,
  clicks a card that is not currently focused, and asserts the top screen is a
  `MemberDetailScreen` for that member and the card holds focus — mirroring the
  existing `Enter` test.

Risk: minimal — additive event handler on one widget, reusing the existing,
tested modal-push path; no data-layer or contract change.
