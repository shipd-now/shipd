# board-header
Status: verified
Epic: update-ui-look-feel

## Idea

Replace the delivery board's stock textual `Header` and demo-era checkbox
controls strip with a Shipd-style header bar — brand block, centered live
search, an `epic`/`initiative`/`none` segmented grouping control, and a
heartbeat-derived autopilot indicator — introducing the three-state grouping
mode.

### Motivation

board-theme landed the palette but the board still opens on textual's stock
`Header` plus a checkbox strip, and grouping is a boolean that cannot surface
the initiative grouping `build_board` already computes. This member ports the
epic's "header bar" design region: product-style chrome and the
epic/initiative/none grouping mode.

### Details

- One `#header-bar` row replaces both the stock `Header()` and
  `#controls-strip`: brand block, the existing search input/✕/match-count
  cluster (re-homed, ids unchanged), the segmented grouping control, the
  autopilot indicator, and the existing `HeaderChart`.
- `group_mode` (`epic` | `initiative` | `none`, default `epic`) replaces the
  `group_by_epic` boolean; `g` cycles, the segmented control selects directly,
  the palette's grouping command cycles through the same path.
- `initiative` mode mounts collapsible per-initiative lane groups fed by the
  board's existing `groups` buckets; no run/open controls on those headers.
- A pure `autopilot_live(board)` predicate (heartbeat `running` +
  `updated_at` within 3600 s, the statusline's window) drives a `●
  autopilot on` / idle indicator, re-evaluated each interval refresh.

Affected capabilities: `delivery-dashboard` (modified: `board-tui`,
`board-epic-grouping`, `board-search`, `board-command-palette`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (0.6.52 → 0.6.53). No new
dependencies; the stdlib-only `tests/` suite is untouched.

### Non-goals

- No filter strip, chips, totals, synced-ago, or shipped-this-week stats
  (board-filters); no modal restyle (board-modals); no row/lane-band redesign
  (board-rows, in flight — rebase this branch after it merges, before build).
- No data-layer changes: `build_board`, `member_actions`, the pure launch
  builders, and the heartbeat format are untouched; the indicator is a
  read-only derivation.
- No persistence of the grouping mode or query across relaunches.

## Implementation

- **Header bar layout — three zones.** `compose` drops `yield Header()` and
  the controls strip and yields `Horizontal(id="header-bar")` containing:
  `#brand` (`Static`, content markup
  `[$accent bold]shipd[/] [$fg-muted]delivery board[/]`); a
  `#search-cluster` `Horizontal` (`width: 1fr; align-horizontal: center`)
  wrapping the existing `SearchInput`/`#board-search-clear`/
  `#board-search-count` (ids and handlers unchanged, so the board-search
  behavior and its tests carry over); a `#group-mode` `Horizontal` of three
  `Button`s `#group-mode-epic|initiative|none` (class `mode-button`: height 1,
  border none, auto width; active mode carries `mode-active`, styled
  `background: $primary 25%`); `#autopilot-indicator` (`Static`); and the
  existing `HeaderChart` (board-throughput-chart says only "the board TUI
  header", so no delta there). Bar CSS: `height: auto; background: $surface`.
  Rejected: keeping the stock `Header` above the bar — two chrome rows of
  redundant title.
- **Mode state.** `GROUP_MODES = ("epic", "initiative", "none")` module
  constant; `self.group_mode = "epic"` replaces `group_by_epic`.
  `action_cycle_grouping` (the `g` binding, description `Group`) advances
  cyclically and calls `_set_group_mode(mode)`, which updates the buttons'
  `mode-active` class and awaits `_render_lanes()`. Mode buttons carry a
  `group_mode_value` attribute; `on_button_pressed` routes it before the
  epic-slug checks (mirroring the `board-search-clear` early return).
  `action_toggle_grouping`, `on_checkbox_changed`, and the `Checkbox`/`Header`
  imports go. The palette `SystemCommand` becomes ("Cycle grouping", "Cycle
  the lanes' grouping: epic → initiative → none",
  `self.action_cycle_grouping`). Rejected: a `RadioSet` — renders radio
  bullets, not the mock's segmented look.
- **Signature.** `_lane_signature(cards, group_mode, search_query)` — the
  second parameter becomes the mode string (bool → str is signature-breaking
  only for tests, which are amended). `_render_lanes` branches:
  `epic` → `_mount_epic_groups`, `initiative` → `_mount_initiative_groups`,
  `none` → flat cards — the empty-lane branch (the `.lane-empty` mount) stays
  first, ahead of the mode dispatch, exactly as today.
- **Initiative mounting.** `_mount_initiative_groups(lane, lane_name, cards)`
  walks `self.board["groups"]` in order; for each group it collects that
  group's epics' card specs from the lane's (already search-filtered) list,
  preserving lane order, and mounts one `Collapsible`
  (`classes="epic-group lane-item"` — `lane-item` so the repaint's
  `remove_children(".lane-item")` clears it while the docked `.lane-header`
  band survives, matching the epic-mode mounts;
  `id="init-group-<lane>-<slug or workspace>"`, `collapsed=False`) titled by
  the pure helper `initiative_group_title(initiative)` → `"<slug> [<status>]"`
  or `"workspace"` for `None`. No run/open buttons, so plain `Collapsible`
  mounts (no `EpicGroupRow`); a group with no kept cards mounts nothing,
  which satisfies the generalized fully-filtered-group scenario. Rejected:
  regrouping from per-card epic lookups without `groups` — re-derives what the
  aggregation already provides.
- **Autopilot indicator.** In the dependency-free pure-renderers section (next
  to `epic_stalled`): `AUTOPILOT_FRESH_SECONDS = 3600` and
  `autopilot_live(board, now=None)` — true when any epic's `heartbeat` has
  `state == "running"` and `now - updated_at <= AUTOPILOT_FRESH_SECONDS`
  (missing `updated_at` → not live). `refresh_board` updates the indicator
  after re-aggregation via a query-empty-safe loop (the match-count pattern):
  live → `[$success]●[/] autopilot on`, idle → `[$fg-subtle]○ idle[/]`.
  Rejected: file-mtime probing like the statusline — the board already parses
  the heartbeat JSON, and `updated_at` is the spec'd liveness field.
- **Tests.** All in `plugins/s/skills/build/tests_textual/test_dashboard.py`
  (pure helpers included,
  matching `epic_stalled`'s placement — they sit below the module's `textual`
  import): amend the ~9 controls-strip/Checkbox assertions and the
  `_lane_signature` boolean tests; add header-bar chrome, mode-cycling,
  mode-button, initiative-grouping, and indicator tests. The stdlib `tests/`
  suite needs no change.

Risks: the centered zone layout is terminal-cell math — guarded by asserting
widget presence/ids, never pixel columns; `board-rows` (in flight) edits
adjacent group-header code — guarded by rebasing this branch on `main` after
it merges, before build starts.
