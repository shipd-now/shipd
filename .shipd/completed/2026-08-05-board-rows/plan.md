# board-rows
Status: verified
Epic: update-ui-look-feel

## Idea

Redesign the delivery board's lane content to the Shipd density: one-row task
rows with risk-coloured glyphs and live stage, one-row epic group headers
carrying a per-lane member count, a tinted per-lane header band, and per-lane
empty-state texts.

### Motivation

board-theme landed the Shipd palette, but the lanes still render demo-era
content: padded multi-row cards with accent bars, group headers wrapped in
border and padding rows, lanes titled by a dim border label, and blank columns
when empty. This member ports the epic's "lane content" design region — the
dense one-row issue rows and tinted lane chrome of the Shipd mock.

### Details

- `TaskCard` renders one row: a risk-coloured `●` glyph (via the `$risk-*`
  theme variables), the slug (search highlighting preserved), and the live
  stage in the muted tier while the member is driven; shipped rows swap the
  glyph for a subtle-tier `✓`. The accent bars and inter-card margin go.
- Epic group headers become a single row — the Collapsible's top-border and
  bottom-padding rows removed, the inline run/open controls re-pinned to the
  title row — and the title gains the count of that epic's cards in the lane.
- Each lane gets a one-row tinted header band (label and band coloured by its
  `$lane-*` variable), replacing the border title; the band is docked, so it
  neither scrolls nor is torn down by lane repaints.
- A lane mounting no rows shows its own per-lane empty-state text.

Affected capabilities: `delivery-dashboard` (modified: `board-tui`,
`board-epic-grouping`, `board-shipd-theme`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (0.6.47 → 0.6.48). No new
dependencies; the stdlib-only `tests/` suite is untouched.

### Non-goals

- No header bar, grouping segmented control, or search-input re-homing
  (board-header); no filter strip or totals (board-filters) — and no member
  count in the lane header band (oracle-settled: counts belong to the epic
  group headers now and to board-filters' totals later).
- No modal restyling (board-modals) and no palette changes (board-palette).
- No data-layer changes: `build_board`, `member_actions`, the pure launch
  builders, `_lane_signature`'s fields, and the heartbeat format are
  untouched.
- The group header keeps its `[status]` token (oracle-settled: the spec
  mandates slug and status) and the stall `✗` marker unchanged.

## Implementation

- **Row text is content markup, not CSS.** `TaskCard._card_text` returns
  `"[$risk-high]●[/] <slug>"` (medium/low likewise; a missing or unknown risk
  renders `[$fg-muted]●[/]`), with `"[$fg-muted] · <stage>[/]"` appended while
  the entry is driving; a shipped row (`_member_column(member, entry) ==
  "shipped"`) renders `[$fg-subtle]✓[/] <slug>` instead. Custom theme
  variables resolve in Content markup through the same merged-variables path
  the existing `[$text-error]✗[/]` stall marker and `[$accent]` search
  highlight already use; a mounted-app test asserts the resolution. Rejected:
  per-risk CSS classes — CSS cannot colour a span of a Static's content.
- **Row CSS:** drop the `TaskCard` `border-left` accent bars, the `.risk-*`
  border rules, the `add_class("risk-%s")` call (nothing consumes the class
  any more), and the `margin: 0 0 1 0`; add `height: 1` so a long slug clips
  instead of wrapping. `padding: 0 1` and the `TaskCard:focus` accent rule
  stay.
- **One-row group header:** override the pinned textual 8.2.8 Collapsible
  defaults in `.epic-group`: `border-top: none; padding-bottom: 0;` —
  `padding-left: 1` is deliberately kept so `EpicGroupRow`'s after-title
  x constant (5 cells of title-row chrome) stays valid — plus
  `.epic-group Contents { padding: 0 0 0 2; }` (default `1 0 0 3`) for dense
  indented rows. With the top-border row gone the title sits at y 0, so both
  offset assignments in `EpicGroupRow` (constructor and `on_resize`) change
  `(x, 1)` → `(x, 0)`. Rejected: replacing Collapsible with a custom header
  widget — larger churn and it re-implements collapse for no visual gain.
- **Header count:** `epic_group_title` gains a keyword-only `count=None`
  parameter appending `" · %d"` after the initiative segment;
  `_mount_epic_groups` passes `len(group_cards)`. `count=None` keeps today's
  output byte-identical, so the stall-marker tests and `EpicGroupRow`'s
  width measurement are unaffected by the default path.
- **Lane header band:** `Lane.compose` yields
  `Static(self.lane_name.upper(), classes="lane-header")` and the
  `border_title` assignment is dropped. CSS: `.lane-header { dock: top;
  height: 1; padding: 0 1; text-style: bold; }` plus five per-lane blocks
  `#lane-<name> .lane-header { background: $lane-<name> 15%; color:
  $lane-<name>; }`. A docked child is excluded from the scroll region, so the
  band stays pinned. Rejected: wrapping Lane in a Vertical with a separate
  scroll body — a bigger diff that breaks the `card.parent` assumption in
  `move_card_focus`.
- **Repaint-safe clearing:** everything `_render_lanes` mounts into a lane
  carries the class `lane-item` — flat-mode `TaskCard`s, `EpicGroupRow`s, and
  the empty-state Statics — and the lane clear becomes
  `lane.remove_children(".lane-item")`, so the docked header band survives
  every repaint. Grouped-mode cards live inside the Collapsible and need no
  class. Rejected: a `*:not(.lane-header)` selector (unsupported) and
  child-index slicing (fragile).
- **Empty states:** a module-level `LANE_EMPTY_TEXTS` dict — unplanned
  "nothing unplanned", ready "nothing ready", building "nothing building",
  review "nothing in review", shipped "nothing shipped yet" — mounted as
  `Static(..., classes="lane-empty lane-item")` when the lane's filtered
  content is empty, styled `color: $fg-subtle; text-style: italic;
  padding: 0 1;`. The same text serves the search-filtered-empty case; the
  empty/non-empty flip already changes `_lane_signature`, so no signature
  change is needed.
- **Version bump** 0.6.47 → 0.6.48 in `plugins/s/.claude-plugin/plugin.json`
  (every `plugins/s/` change bumps in its own PR).

Risks: the header-control geometry (title-x constant, y re-pin) is the sharp
edge — guarded by keeping `padding-left: 1` and by the existing overlong-title
clamp tests; theme-variable markup resolution is asserted against a mounted
app before the row work builds on it.
