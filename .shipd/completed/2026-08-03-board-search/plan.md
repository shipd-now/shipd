# board-search
Status: verified
Epic: update-ui-look-feel

## Idea

Add live search to the delivery board's `tui` verb: `/` focuses a search input
in the controls strip, the lanes filter as the user types with the matched
slug span highlighted in accent and a live match count, and `esc`/`✕` clears.

### Motivation

The board renders every member of every epic across five lanes with no way to
narrow it, so finding one change on a busy board means scanning by eye. The
approved `update-ui-look-feel` epic defines live search as one of the board
interactions the Shipd design carries, and `board-search` is the member that
delivers it.

### Details

- A search `Input` joins the existing `#controls-strip` beside the
  group-by-epic toggle, with a compact `✕` clear button and a match-count
  label. (The later `board-header` member re-homes the input into its header
  bar; this change keeps today's chrome.)
- `/` focuses the input from the board; typing filters the lanes live.
- Matching is a case-insensitive substring over member slug, epic slug, and
  initiative slug — view-level only; `build_board` aggregation is untouched.
- A matching card highlights the matched span of its slug in the accent
  style; a match that hits only the epic or initiative keeps the card
  visible without a slug highlight.
- The match-count label shows the number of matching members while a query is
  active and is blank otherwise.
- The query folds into `_lane_signature`: a query edit repaints, an unchanged
  board under an unchanged query repaints nothing, and the active filter
  survives interval refreshes. With grouping on, an epic whose members are
  all filtered out mounts no group header.
- `escape` in the input and the `✕` control clear the query and restore the
  full board.

Affected capability: `delivery-dashboard` (one added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, and the plugin
version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No filter strip, chips, totals, or risk filters — that is `board-filters`.
- No header bar and no input re-homing — `board-header` moves the input later
  and carries that delta.
- No highlighting inside epic group header titles; highlighting is card-level.
- No persistence of the query across runs; no change to `build_board`
  aggregation, the heartbeat format, or the pure launch builders.
- No command palette — `board-palette` owns `^p`.

## Implementation

- **Placement — the existing controls strip, not a new header bar.** The
  epic's design homes search in `board-header`'s header bar, but the
  autopilot delivers members risk-ascending, so `board-search` (low) lands
  before `board-header` (medium). The input therefore mounts self-contained
  in `#controls-strip`, and `board-header`'s own delta re-homes it. Rejected:
  blocking on `board-header` — it inverts the delivery order for a purely
  cosmetic placement.
- **Widgets.** A `SearchInput(Input)` subclass (id `board-search-input`) so
  it can carry an `escape` binding that clears-and-refocuses; a `✕` clear
  `Button` (id `board-search-clear`, classes `compact-button`, matching the
  modal close controls' 1×3 style); a match-count `Static`
  (id `board-search-count`). All three mount inside `#controls-strip`.
- **View-level state.** `BoardApp.search_query` (default `""`), updated from
  `on_input_changed` (which then awaits `_render_lanes()`), mirroring how
  `group_by_epic` flows through `on_checkbox_changed`.
- **Pure helpers beside the other signature helpers.**
  `_search_matches(query, epic_slug, initiative, member_slug)` — lowercased
  substring over the three fields, `True` for an empty/whitespace query — and
  `_highlight_slug(slug, query)` — wraps the first matched span in
  `[$accent]…[/]` content markup. `$accent` is a theme variable, so the
  highlight picks up the Shipd palette automatically once `board-theme`
  registers it. Rejected: `[reverse]` — the epic pins "accent".
- **Filtering and repaint.** `_render_lanes` filters each lane's
  `_lane_contents` cards through `_search_matches` (initiative resolved via
  `_find_epic`) before computing signatures and mounting; `_lane_signature`
  gains a third `search_query` argument folded into the tuple like
  `group_by_epic`, so a query edit always repaints (highlights change even
  when the filtered set does not) and an idle refresh under a steady query
  repaints nothing. Grouped mounting is unchanged — a fully filtered epic
  simply contributes no cards, so no header is flushed.
- **Highlight threading.** `TaskCard.__init__` gains a `search_query=""`
  keyword; `_card_text` renders the slug through `_highlight_slug`. Cards are
  reconstructed whenever a lane repaints, and a query change always repaints,
  so construction-time highlighting stays correct.
- **Count and clear.** `_render_lanes` updates `#board-search-count` to
  `"N matches"` (matching members across all lanes) when the query is
  non-empty, else `""`. The `✕` press is routed at the top of
  `BoardApp.on_button_pressed` by button id before the epic-control marker
  checks; clearing sets the input's `value = ""` (which triggers the normal
  changed→repaint path) and refocuses the first `TaskCard` on the board when
  one exists, so arrow-key navigation resumes; `escape` in `SearchInput`
  does the same clear-and-refocus.
- **`/` binding.** An app-level `Binding("slash", "focus_search", "Search",
  key_display="/")` focuses the input — `"slash"` is the pinned textual's
  key name for `/` (`_character_to_key`), and `key_display` keeps the footer
  showing `/`; while the input is focused the card/app keys (`q`, `g`,
  `r`/`l`/`o`) don't fire, which is the standard `Input` capture behavior.

Risk: the controls-strip placement is intentionally temporary; the follow-up
`board-header` member owns the move, so nothing here hard-codes layout beyond
the strip. The stdlib-only `tests/` suite is untouched — every new helper
lives in `dashboard.py`, whose import already requires `textual`, and all new
tests go to `tests_textual/`.
