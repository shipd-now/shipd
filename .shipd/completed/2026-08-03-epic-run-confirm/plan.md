# epic-run-confirm
Status: verified

## Idea

Two safety additions to the board's epic-header **▶ run** control:
1. **Guard** — only render the run control on **runnable** epics (status
   `ready`/`active` with at least one `unplanned`/`ready` member). A
   `complete`/`archived` epic gets no run control, so it can't be run from the
   board at all.
2. **Confirm** — clicking a run control no longer dispatches immediately; it opens
   a modal "This will deliver the full epic, are you sure you want to continue?"
   with **Yes** / **No** controls and a **✕ close control in the top-left**. The
   epic-level autopilot is dispatched only on **Yes**; **No**, **✕**, and
   `Escape` dismiss it without running.

### Motivation

The run control shipped on *every* epic header, including closed epics. A stray
click on a `complete` epic spawns an autopilot that the status guard
(`autopilot.run`, "not ready/active") immediately rejects — harmless, but
confusing and easy to trigger by accident (the user just did). Hiding the control
where it can't do anything, and gating the real, expensive "deliver the whole
epic" action behind an explicit confirmation, removes both the accidental
no-op and the risk of an accidental *real* run on a live epic.

### Details

- **Runnable predicate:** `status in {ready, active}` AND any member's board
  `state in {unplanned, ready}`. This mirrors what `autopilot.run` accepts (status
  guard) and what it actually drives (unplanned/ready members) — a live epic with
  nothing left to drive also shows no control.
- **Confirmation modal:** a small centred `ModalScreen` carrying the epic slug,
  with the exact prompt text, a Yes control, a No control, and a ✕ close control
  positioned top-left. Yes → dispatch the epic run then dismiss; No / ✕ / Escape →
  dismiss only.

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py` (a stdlib runnable
predicate; the run-control mount in `_mount_epic_groups`; a new
`EpicRunConfirmScreen`; the run-button handler routes through it), a **stdlib**
test for the predicate in `tests/`, **textual** tests in `tests_textual/`;
plugin version bump.

### Non-goals

- No change to the group visuals, collapse behavior, initiative header, the
  toggle, the lanes, or the card spec-detail modal.
- No change to the autopilot itself or the epic-run **launch builder** — only
  *when/whether* `dispatch_epic_run` is called changes.
- No per-member run confirmation (this is the epic-level run only).
- The confirmation is not remembered/suppressible — every run click confirms.

## Implementation

- **Runnable predicate (stdlib, testable).** Add a pure module-level helper —
  e.g. `epic_is_runnable(epic)` — returning `True` iff
  `(epic.get("status") in ("ready", "active"))` and
  `any(m.get("state") in ("unplanned", "ready") for m in epic.get("members", []))`.
  No `textual`; place it near the other stdlib helpers and unit-test it in
  `tests/`.
- **Guard the run control.** In `_mount_epic_groups`, only build and mount the
  `▶` run `Button` when `epic_is_runnable(_find_epic(self.board, group_slug))`.
  When not runnable, mount the group with the `Collapsible` alone (no run button,
  no behavioral change to collapse/visuals). The group row still renders; only
  the run affordance is conditional.
- **Confirmation modal.** Add `EpicRunConfirmScreen(ModalScreen)`, constructed
  with the epic slug. `compose` yields a centred `Container` with: a top-left
  `Button("✕", id="epic-run-close")`, a `Static` with the exact text "This will
  deliver the full epic, are you sure you want to continue?", and a `Yes`
  (`id="epic-run-yes"`) / `No` (`id="epic-run-no"`) button pair. Bind `escape` →
  dismiss (mirroring `MemberDetailScreen`'s dismiss action). Its
  `on_button_pressed`: `epic-run-yes` → `self.app.dispatch_epic_run(self.epic_slug)`
  then `self.dismiss()`; `epic-run-no` / `epic-run-close` → `self.dismiss()` only.
  CSS: small centred box (`align: center middle`, a modest fixed/auto size), with
  the ✕ laid out at the top-left of the box (e.g. its own top row before the
  prompt).
- **Route the run button through the modal.** Today `BoardApp.on_button_pressed`
  reads `event.button.epic_slug` and calls `dispatch_epic_run` directly. Change it
  to `self.push_screen(EpicRunConfirmScreen(slug))` instead — the actual dispatch
  now happens only from the modal's Yes handler. `dispatch_epic_run` itself is
  unchanged. (The modal's own buttons are handled by `EpicRunConfirmScreen.
  on_button_pressed` because the modal screen is on top of the stack; keep the
  board's handler scoped to the `epic_slug`-carrying run buttons only.)
- **Import** any newly-referenced widget names (all of `Button`, `Static`,
  `Container`, `ModalScreen`, `Binding` are already imported) — no new textual
  imports are expected; add one only if you reference a not-yet-imported name.

### Test seams

- **Stdlib (`tests/`).** `epic_is_runnable` truth table: ready+unplanned → True;
  active+ready → True; ready with only shipped/archived members → False; complete
  (any members) → False; active with no members → False.
- **Textual (`tests_textual/`).** With grouping on: a runnable epic's header has a
  run `Button`; a `complete`/no-drivable epic's header has none. Clicking a run
  button pushes `EpicRunConfirmScreen` and does NOT dispatch (assert via the
  injectable launch/dispatch seam — zero launches yet) and leaves the group's
  `collapsed` unchanged. Activating Yes dispatches exactly one epic-level run and
  dismisses; activating No / ✕ / pressing Escape dismisses with zero dispatches.
  Verify the modal shows the exact prompt string.

Risk: low-to-moderate — additive predicate + one new modal screen + a one-line
change to the run-button handler; the autopilot, launch builder, grouping
visuals, and collapse behavior are all untouched.
