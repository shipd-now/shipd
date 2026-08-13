# modal-chrome-widths
Status: verified

## Idea

Fix the modal badge chips stretching to full width (pushing their siblings
outside the modal), keep the focused ✕ on the accent title bar's color
scheme, and add a containment sweep test so this class of layout bug fails CI
instead of reaching the board.

### Motivation

`.modal-badge` chips have no `width: auto`, so each takes textual's default
100% width: the first chip renders as a full-row band and every later chip
(lane, stage, epic) is laid out entirely outside the modal container —
invisible — in both the spec-detail and epic-detail modals; separately, the
auto-focused ✕ close control picks up the theme's focused-Button styling and
breaks the accent title band. This is the third recurrence of the
default-width bug class (GraphOption, then group headers), so it also needs
a durable regression guard.

### Details

- `.modal-badge` gets `width: auto` so every chip hugs its text and the
  badge rows show all their chips inside the modal.
- `.modal-title-bar .compact-button:focus` keeps the accent scheme (dimmed
  like hover) so the focused ✕ never breaks the band.
- A reusable containment sweep in `tests_textual` opens each modal
  (spec-detail with risk+stage+epic, epic-detail with members, run-confirm,
  graph config) and asserts every `Button`, `.modal-badge`, and
  `.modal-title-text` region sits inside its screen's container.

Affected capabilities: `delivery-dashboard` (added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No content or wiring changes to any modal — chrome geometry and the focus
  color only.
- No changes to the group headers or graph dialog (already flex-fixed);
  they are covered by the sweep, not modified.

## Implementation

- **Badge width**: extend the existing app-level `.modal-badge` rule with
  `width: auto;` — one rule fixes every chip site (member modal badge row,
  epic modal badge row, `EpicMemberRow` lane chips). Rejected: per-site
  rules — the shared class is the single source.
- **Focus scheme**: add `.modal-title-bar .compact-button:focus {
  background: $accent-dim; color: $background; }` beside the existing hover
  rule in each modal's CSS (member, epic, run-confirm) — the focused ✕ then
  matches the hover treatment instead of the theme's dark Button focus.
- **Containment sweep**: one test helper `assert_chrome_contained(screen)`
  in `tests_textual/test_dashboard.py` that queries `Button`,
  `.modal-badge`, and `.modal-title-text` on the given screen and asserts
  each widget's region is inside the screen's `Container` region and has
  nonzero width; parameterized tests open all four screens (spec-detail
  with a risk+driving-stage+epic member so all four chips render,
  epic-detail with members, run-confirm, graph config) and run the sweep.
  The sweep would have caught GraphOption, the header overlays, and this
  bug.
- **Risk**: `width: auto` on chips relies on padding for the pill shape —
  the existing `padding: 0 1` keeps them 2 cells wider than their text,
  matching the mock.
