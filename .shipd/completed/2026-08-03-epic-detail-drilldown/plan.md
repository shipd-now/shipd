# epic-detail-drilldown
Status: verified

## Idea

Make the member-spec rows in the **epic-detail modal** clickable: clicking one
opens that change's own **spec-detail modal** (the same `MemberDetailScreen` a
lane card opens), pushed on top of the epic-detail modal so dismissing it returns
to the epic. This completes the drill path epic → change that the
`epic-detail-dialog` change deliberately deferred as a follow-up.

### Motivation

The epic-detail modal lists an epic's member specs but they are inert text — to
read one you have to close the modal, find the card in a lane, and click it.
Since the board already has a rich spec-detail modal for a change, the epic's
member list should link straight into it, so a user can browse an epic and drill
into any of its changes without leaving the dialog.

### Details

- Each member row in the epic-detail modal becomes a **clickable, focusable
  widget** that still shows `<slug>  [<risk>]  <state>` (risk visible), and on
  click opens `MemberDetailScreen` for that member.
- The member modal is **stacked** on top of the epic-detail modal (push, not
  replace); its ✕/`Escape` returns to the epic-detail modal.

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py` (a small clickable
member-row widget; `EpicDetailScreen.compose` resolves each member's heartbeat
entry and yields the row widget), **textual** tests in `tests_textual/`; plugin
version bump. No data-layer change.

### Non-goals

- No change to the epic-detail modal's header, overview (epic.md Markdown),
  dismissal, the open/run controls, grouping, or the lane cards.
- No change to `MemberDetailScreen` itself — it is reused unchanged.
- No new drill targets beyond the member spec-detail modal (e.g. no epic→epic).

## Implementation

- **Clickable member-row widget.** Add a small widget — e.g.
  `EpicMemberRow(Static)` — constructed with `(epic_slug, member, entry,
  epic_status)`. Set its label to `"%s  [%s]  %s" % (slug, risk or "?", state or
  "?")` with **`markup=False`** (so the bracketed risk is not swallowed by Rich
  markup — the same fix the epic-detail header/rows already use), `can_focus =
  True`, and give it a class (e.g. `epic-member-row`) for a focus/hover
  affordance. Its `on_click(self, event)` calls
  `self.app.push_screen(MemberDetailScreen(self.epic_slug, self.member,
  self.entry, self.epic_status))` — reusing the exact modal a `TaskCard` opens.
  (Mirror `TaskCard.on_click` → the existing spec-detail push path.)
- **Wire it in `EpicDetailScreen.compose`.** Where the modal currently yields a
  `Static` per member, instead: resolve the epic's heartbeat roster once via
  `roster = _roster_by_slug(epic.get("heartbeat"))`, and for each member yield
  `EpicMemberRow(self.epic_slug, member, roster.get(member["slug"], {}),
  epic.get("status"))`. Keep the empty-list "no specs" notice. Everything else in
  the modal (header, rules, Markdown overview, close handling) is unchanged.
- **Stacking semantics.** `push_screen` places the `MemberDetailScreen` above the
  `EpicDetailScreen`; the member modal's existing `Escape`/`✕` `dismiss()` pops
  back to the epic-detail modal — no new dismissal code needed.
- **Imports.** `Static`, `MemberDetailScreen`, and `_roster_by_slug` already
  exist; `EpicMemberRow` is a new class defined near `TaskCard`/`EpicDetailScreen`
  inside the guarded `textual` block (it subclasses `Static`). No new textual
  import expected.

### Test seams (tests_textual)

- Open an epic-detail modal (via the open control) for an epic with members;
  assert the member rows are `EpicMemberRow` instances and their **rendered** text
  (`str(row.render())`) still contains the risk in brackets and the state.
- Click a member row: assert a `MemberDetailScreen` for that member's slug is
  pushed onto the screen stack **on top of** the `EpicDetailScreen` (the epic
  modal is still in the stack beneath), and that dismissing the member modal
  (`Escape`) returns to the `EpicDetailScreen`.
- Point `root`/`board_fn` at a fixture whose member maps to an on-disk change
  (or accept the not-yet-planned notice inside the member modal) — the drill
  target is `MemberDetailScreen`, which is already tested; here only the push
  from the epic modal is new.

Risk: low — one small additive widget and a compose change reusing the existing,
tested `MemberDetailScreen` and `_roster_by_slug`; no data-layer or
`MemberDetailScreen` change, and the markup=False lesson from the prior change is
carried forward on the new row.
