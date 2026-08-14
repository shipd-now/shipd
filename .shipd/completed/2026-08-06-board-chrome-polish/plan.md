# board-chrome-polish
Status: verified

## Idea

Polish the lane-row chrome: the per-lane count becomes a muted bracketed
suffix in the group title, header controls stop glowing when idle, the group
band runs unbroken to its divider, long card slugs ellipsize instead of
blanking, and the containment sweep extends to the board screen.

### Motivation

Live use surfaced four rough edges: the trailing count Static reads as an
unexplained digit kissing the scrollbar; the idle run/open controls' 25%
accent tint reads as a stuck hover state; the group's panel background stops
at its last card leaving a black gap before the divider; and a card whose
`✓ <slug>` text is one cell wider than the card word-wraps onto a cropped
second line, rendering as a bare `✓` with the slug invisible.

### Details

- `epic_group_title` renders the count as a ` (N)` suffix in the muted
  foreground; the trailing `.epic-count` Static and its CSS are removed
  (all group headers — epic, standalone, initiative-mode — use the title
  suffix).
- `.compact-button`'s idle background becomes the neutral `$bg-hover`; the
  accent tint appears only on hover and focus. Modal ✕ accent overrides are
  unchanged.
- The group band's panel background extends to the divider (no black gap
  after the last card).
- `TaskCard` (and the epic modal's `EpicMemberRow`) get single-line
  nowrap + ellipsis text so an overlong slug clips visibly.
- The chrome-containment sweep gains a board-screen variant run at two
  widths.

Affected capabilities: `delivery-dashboard` (modified `board-epic-grouping`,
added `lane-row-presentation`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to what the count means or when controls render; presentation
  only.
- No scrollbar-region changes (the deferred "gray box after margin"
  investigation stays open).
- No modal chrome changes beyond `EpicMemberRow`'s nowrap.

## Implementation

- **Count in title.** `epic_group_title(..., count=N)` appends
  ` [$fg-muted](N)[/]` (markup) instead of the plain ` · N` of the old form;
  `_mount_epic_groups`/`_mount_initiative_groups` pass `count=` again and
  stop appending the `.epic-count` Static (delete its CSS). The title
  already carries markup (`[status]`, the stall `✗`), so the muted-suffix
  markup rides the same rendering path. Ellipsis on a narrow lane truncates
  the suffix last-first, which is acceptable.
- **Idle tint.** In the app-level `.compact-button` rule, `background:
  $primary 25%` → `background: $bg-hover`; add `.compact-button:focus {
  background: $primary 50%; }` beside the existing hover rule so keyboard
  focus reads like hover. The `.modal-title-bar .compact-button` accent
  overrides (base/hover/focus) already out-rank the shared rule.
- **Band continuity.** The black gap is the area between the Collapsible's
  last card and the row's bottom border: give `.epic-group-row`
  `background: $panel` so the full row box (including the gap the
  Collapsible does not paint) carries the band color to the divider.
- **Card ellipsis.** App CSS: `TaskCard { text-wrap: nowrap;
  text-overflow: ellipsis; }` and the same pair on `.epic-member-row` —
  one painted line always carrying the slug prefix; no wrapped-and-cropped
  blank rows.
- **Board sweep.** Reuse `assert_chrome_contained`'s approach in a
  board-screen variant: for every lane, assert each `EpicGroupRow`'s
  buttons sit inside the lane's scrollable content region, and every
  `TaskCard`'s first painted line contains the start of its slug (catches
  the wrap-blank bug); run it at widths 160 and 120.
- **Risk**: markup in the count suffix must not be double-escaped where
  titles pass through `Collapsible` (the existing `[status]`/`✗` markup
  proves the path); the sweep pins it.
