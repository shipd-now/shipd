# board-parked-member-signal
Status: verified

## Idea

Make a parked member on the delivery board — one the autopilot could not ship —
obvious at a glance, and surface the validation output that parked it clearly
in its spec-detail modal, instead of letting it read as an idle or mid-flight
card.

### Motivation

When the autopilot rejects a member (e.g. `docapp-reminders`, parked
`context insufficient (gate exit 2); oracle enrichment failed: …`) the board
gives no signal that anything is wrong. `TaskCard._card_text` only special-cases
`shipped` (`✓`) and `driving` (`● slug · <stage>`); a `rejected` or
`needs-human` member falls through to a bare `● slug`, identical to an idle
ready card. Its spec-detail modal is worse than silent: the badge row shows a
`building` lane chip (rejected maps to the `building` lane) and a muted
`stage: gate` chip pulled from the leftover roster stage — so a dead, rejected
run reads as if it is *currently gating*. The one field that explains it,
`entry["reason"]` (written by `heartbeat.py`'s `member_finished`), is rendered
nowhere; you only learn the truth by reading `Status: rejected` inside the Plan
tab body.

The data is already on the roster entry — the board simply does not surface it.
A small, member-scoped signal (a card marker glyph + an honest modal badge +
a highlighted reason callout) turns a silent park into an obvious one.

### Details

- **Member-scoped only.** This does not touch `board-stall-signal`. A rejected
  member does not raise the epic-level `✗` marker or the whole-epic Retry
  banner — the attention lands on the member's own card and modal, so the fix
  framing stays "re-plan this change", not "retry the whole epic".
- **Distinct glyph per parked kind** in the theme's error tier: `rejected` →
  `⚠`, `needs-human` → `⛔`, dead-run `stale` → `†` (carrying the death age
  dead-run detection already computes). A normal card is unchanged.
- **State word on the card, full reason in the modal.** The card carries only
  the short state label after the slug; the full `reason` string lives in the
  modal callout, keeping every card a single terminal row.
- **Honest modal badges.** The muted live-stage chip renders only while the
  member is actually being driven (this already matches `board-modal-chrome`'s
  wording; the code currently shows it whenever a leftover stage is present).
  A parked member shows an error-tier state chip instead, and — when its entry
  carries a `reason` — a tinted accent-bar callout above the artifact tabs,
  the member-level analogue of the epic stall banner.

### Non-goals

- **The token/throughput graph replaying a dead session as "recent".** That the
  header/modal chart pins a dead session's last sample flush-right with no
  silence gap is a real but separate defect, deliberately out of scope here.
- **Epic-level escalation of rejected members.** Left to `board-stall-signal`'s
  existing `needs-human`-only rule; changing it is a separate decision.
- **Auto-recovery of the oracle-enrichment crash** (`session CLI exited 1`).
  This change makes the failure visible; diagnosing the crash is separate work.

## Implementation

A single new pure predicate feeds both the card and the modal, reusing existing
theme variables and the epic stall banner's tinted accent-bar pattern:

- `member_signal(member, entry)` — a dependency-free predicate placed with the
  other pre-`textual` board helpers (near `_member_column`), so it is
  unit-testable under the system `python3` with `textual` absent, in the stdlib
  `tests/` suite. It returns `{"kind", "glyph", "label", "reason"}` for a
  parked member (checking `entry["stale"]` first, then `rejected` /
  `needs-human` from the entry or worktree-derived board state) and `None`
  otherwise.
- `TaskCard._card_text` renders the signal glyph (error tier) + slug + muted
  state label for a parked member, ahead of the existing risk-glyph / driving
  branches; shipped and driving cards are unchanged.
- The spec-detail modal's badge row shows an error-tier state chip for a parked
  member and guards the muted stage chip to the `driving` state; when the entry
  carries a `reason`, a `member-signal-callout` (error 10% background, solid
  error one-cell left bar, warning-tier reason text) mounts above the artifact
  tabs.
- New CSS: a `.badge-error` chip class beside `.badge-muted`, and the
  `member-signal-callout` rules in `MemberDetailScreen.CSS`, all through `$`
  theme variables.
- Because this edits `plugins/s/`, the plugin version is bumped in
  `plugins/s/.claude-plugin/plugin.json`.
