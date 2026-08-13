# board-filters
Status: verified
Epic: update-ui-look-feel

## Idea

Add the Shipd filter strip to the delivery board TUI: full-board totals,
removable risk/epic/initiative filter chips with an `f` add-filter picker,
and read-only synced-ago / shipped-this-week stats.

### Motivation

The board can search but not filter: the mock's strip — totals, removable
risk/epic/initiative chips, synced-ago and shipped-this-week stats — has no
counterpart, and the palette's planned filter-clearing command has nothing to
clear. This member ports the epic's "search & filter strip" design region.

### Details

- A `#filter-strip` row mounts between `#header-bar` and the `#body` lanes:
  full-board totals, the active filter chips plus a `+ filter` affordance,
  `▲ N shipped this week`, and `synced Ns ago`.
- `f` (and `+ filter`) opens a modal picker of not-yet-active options — risk
  `high`/`medium`/`low`, each epic slug, each initiative slug; selecting one
  adds a removable chip; clicking a chip removes it.
- Chips are view-level state with faceted semantics (same-kind OR, cross-kind
  AND, ANDed with the live search query), folded into the diff-aware lane
  signatures exactly as the search query is.
- The command palette gains a "Clear filters" command, offered only while
  chips are active (mirroring clear-search).

Affected capabilities: `delivery-dashboard` (added: `board-filter-strip`;
modified: `board-command-palette`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/skills/build/tests/test_metrics_view.py`,
`plugins/s/.claude-plugin/plugin.json` (0.6.54 → 0.6.55). No new
dependencies; `build_board` aggregation is untouched.

### Non-goals

- No modal restyle (board-modals, in flight) — the picker uses the board's
  existing modal idiom and inherits that restyle later.
- No persistence of chips across relaunches; no filter kinds beyond
  risk/epic/initiative; no free-text filter values.
- No data-layer changes: `build_board`, `member_actions`, the launch
  builders, and the heartbeat format are untouched; shipped-this-week and
  the autopilot signal stay read-only derivations.
- No change to the search behavior itself — chips only compose with it.

## Implementation

- **Filter state — faceted chips.** `self.filters = []` on `BoardApp`: an
  ordered, duplicate-free list of `(kind, value)` tuples, kinds
  `"risk" | "epic" | "initiative"`. Pure `_filter_matches(filters, epic_slug,
  initiative, member)` beside `_search_matches`: group active chips by kind;
  a member passes when, for every kind present, it matches at least one of
  that kind's values (`risk` → `member["risk"]`, `epic` → its epic slug,
  `initiative` → its epic's initiative slug); empty filters match everything
  (oracle-settled: same-kind OR, cross-kind AND). Rejected: AND across all
  chips — a second same-kind chip could never widen, making chips useless as
  a facet.
- **Filtering path.** `_filtered_lane_contents` keeps a card spec only when
  `_filter_matches(...)` **and** `_search_matches(...)` pass, so fully
  filtered groups mount no header and emptied lanes show their empty-state
  text through the existing branches. `_lane_signature` grows a trailing
  `filters=()` parameter appended into the signature header (beside
  `group_mode`/`search_query`); `_render_lanes` passes `tuple(self.filters)`
  — a chip change always repaints, an idle refresh under steady chips never
  does.
- **Strip chrome.** `compose` yields `Horizontal(id="filter-strip")` between
  the header bar and `#body`: `#board-totals` (`Static`), `#filter-chips`
  (`Horizontal` of chip `Button`s plus the `#filter-add` "+ filter" button),
  `#board-shipped` (`Static`), `#board-synced` (`Static`). CSS uses theme
  variables only: strip `height: auto; background: $surface`; `.filter-chip`
  mirrors `.mode-button` (height 1, border none, auto width,
  `background: $primary 25%`). Totals render
  `"N specs · N epics · N initiatives"` from the **full** board — members
  summed across epics, epic count, distinct initiative slugs from
  `board["groups"]` — never the narrowed view (oracle-settled: the search
  match count already reports the narrowed set).
- **Picker flow.** `Binding("f", "add_filter", "Filter")` on the app;
  `action_add_filter` is inert unless `len(self.screen_stack) == 1`
  (mirroring `action_show_metrics`) and pushes `FilterPickerScreen`, a
  `ModalScreen` composing one `Button` per option from pure
  `_filter_options(board, active)` — risk tiers `high`/`medium`/`low`, then
  epic slugs in board order, then distinct initiative slugs in group order,
  minus already-active chips — each button carrying `chip_kind`/`chip_value`
  and labelled `"<kind>: <value>"`. Its `escape` binding dismisses without
  selecting; pressing an option dismisses the screen then awaits
  `app.apply_filter(kind, value)`. Rejected: a palette-provider flow — the
  epic's key map separates `f` from `^p`, and the palette only clears.
- **Chip lifecycle.** `apply_filter` appends the tuple (no-op when present),
  remounts `#filter-chips` (chips are rebuilt only on filter changes, not per
  tick), and awaits `_render_lanes()`. Chip buttons (`classes="filter-chip"`,
  label `"<kind>:<value> ✕"`) carry `chip_kind`/`chip_value`;
  `on_button_pressed` routes them — and `#filter-add` — before the epic-slug
  checks (the mode-button pattern), removing the chip and repainting.
  `_clear_filters()` empties the list, remounts the (now bare) chip row, and
  repaints; the palette offers `SystemCommand("Clear filters", ...)` on the
  base screen only while `self.filters` is non-empty (the clear-search
  pattern).
- **Stats.** Pure `shipped_this_week(ship_events, now=None)` lands **above**
  the module-scope `textual` import (beside `metrics_view_data`) so it stays
  stdlib-testable: count of events whose `ship_ts` falls on/after the Monday
  (UTC) of `now`'s ISO week, `now` injectable. `refresh_board` calls
  `mtr.collect_ship_events(self.root)` (one jsonl read + one listdir — cheap
  at the 2 s tick; it never raises), stamps `self._last_sync = time.time()`,
  and updates `#board-totals`, `#board-shipped`
  (`"▲ N shipped this week"`), and `#board-synced` via pure
  `_sync_label(last_sync, now=None)` (`"synced Ns ago"` with the `_age`-style
  s/m/h tiers, `"synced ?"` when never) — all through query-empty-safe loops
  (the autopilot-indicator pattern, safe during teardown).

Risk: per-tick `collect_ship_events` re-reads `builds.jsonl`; acceptable now
(the tick already re-aggregates every epic), and the seam is one call site in
`refresh_board` if it ever needs caching. Risk: chip labels colliding with
epic-slug button routing — averted by routing on the `chip_kind` attribute,
never the label.
