# update-ui-look-feel
Status: complete
Theme: developer-experience

## Introduction

The delivery board's `tui` verb works, but it looks like a stock `textual`
application: default theme, round-bordered lanes, multi-line task cards, a
checkbox controls strip. A Claude Design project — "Shipd Board TUI"
(`claude.ai/design/p/ddce95aa-184e-4abf-b8ec-7e92ec2c2fb6`, with its
`colors_and_type.css` design-system tokens) — defines the board's intended
look and feel: a flat dark surface palette with an acid-chartreuse accent,
per-lane color coding, dense one-row issue rows with priority glyphs, an
accent-bar modal style, and a header/footer chrome that reads like a product
rather than a demo. The mock also carries features the board is missing:
live search with match highlighting, a filter strip with removable chips,
grouping by initiative (not just epic), and a command palette.

This epic ports that design to the existing `textual` `BoardApp` in
`plugins/s/skills/build/scripts/dashboard.py` — colors, layout, and the new
interaction features — while preserving every behavior the
`delivery-dashboard` capability already specifies: the five derived lifecycle
lanes, diff-aware refresh, the plan/run/open action launchers, the epic run
confirmation, and the dependency-free helper seams.

Intended outcome: `dashboard.py tui` renders the board in the Shipd design
language, and a user can search (`/`), filter (`f`), regroup (`g` across
epic/initiative/none), and open a populated command palette (`^p`) — with
every new behavior exercised headless in `tests_textual/` and the amended
`delivery-dashboard` spec lint-clean and passing.

Success criteria:

- The Shipd palette drives all board chrome through one registered theme —
  no hard-coded hex scattered across widget CSS.
- Lanes, rows, group headers, modals, header bar, and footer match the mock's
  layout (adapted to terminal cells; fonts stay terminal-controlled).
- Search, filters, three-state grouping, the status extras (autopilot
  indicator, shipped-this-week), and the command palette work end-to-end.
- The existing `tests_textual/` suite passes as amended; the stdlib-only
  `tests/` suite still passes with no `textual` installed.

### Non-goals

- No browser or web UI: the `.dc.html` mock is a visual reference only; the
  deliverable is the `textual` TUI.
- No priority metadata: the existing per-member risk rating is the priority
  signal (no `urgent` tier, no new stub-table column).
- No ID scheme: kebab-case slugs remain the only identity; the mock's
  `SHP-412`/`EP-01` ID columns are not ported.
- No manual lane moves, auto-triage, WIP caps, or in-board member creation —
  the mock's `m move`, "auto-triaged" blurb, `/ 6` cap, and `a add spec` are
  dropped; lanes stay a derived view of lifecycle state.
- No changes to board aggregation semantics, the heartbeat format, or the
  autopilot — new signals are read-only derivations from existing data.
- No font management: terminals own their fonts.
- The epic does not itself plan or build its member changes.

## Decisions

- **One registered theme is the palette's single source.** The design-system
  tokens from `colors_and_type.css` (base/surface/elevated/hover/active
  backgrounds, `#C6FF4E` accent, the red/orange/green/blue/purple semantic
  set, the three foreground tiers) are registered as a custom `textual`
  theme, and all widget CSS references theme variables. Member changes never
  hard-code hex values outside the theme definition.
- **Per-lane color coding follows the mock**: unplanned gray `#8888A0`,
  ready blue `#4DA6FF`, building orange `#FF8C42`, review purple `#9B7FFF`,
  shipped green `#3DCC8E` — used for lane headers (tinted band + colored
  label) and the epic modal's member lane badges.
- **Risk is the priority signal.** The stub-table risk rating colors each
  row's `●` glyph (high=orange, medium=chartreuse, low=dim) and drives the
  risk filter; shipped rows render a dim `✓`. No new metadata.
- **Slugs are the identity.** Rows show slugs; `y` copies the focused slug
  (via `App.copy_to_clipboard`); no minted IDs.
- **Grouping becomes a three-state mode** — `epic` / `initiative` / `none` —
  replacing the boolean `group_by_epic`. The board's existing
  initiative-grouped `groups` data feeds the `initiative` mode. The mode is
  folded into `_lane_signature` so mode flips always repaint, exactly as the
  boolean is today.
- **Search and filters are view-level state.** They live on the App, filter
  what the lanes mount, and are folded into the lane signatures; they never
  persist and never change `build_board` aggregation. Search matches
  substring across slug + epic + initiative, highlighting the matched span
  in accent.
- **Status extras derive from existing data, read-only**: the autopilot
  indicator (green dot / "autopilot on") from any fresh live heartbeat
  (`state: running`, recent `updated_at`); "▲ N shipped this week" through
  the stdlib-only delivery-metrics engine (`metrics.py`), imported the same
  dependency-free way `heartbeat.py` is; "synced Ns ago" from the last
  refresh tick.
- **Spec'd behaviors are preserved, and their scenario amendments travel
  with the member change that alters them.** The five lanes, diff-aware
  per-lane repaint, `plan`/`run`/`open` via the pure launch builders, the
  epic run confirmation flow, and the dependency-free helpers
  (`change_artifacts`, `epic_markdown`, `epic_is_runnable`) all survive.
  Where the redesign changes what an existing `delivery-dashboard` scenario
  asserts (e.g. the checkbox controls strip becoming the header bar), that
  member change carries the spec delta.
- **Modal content stays `Markdown`-rendered.** The mock's token-styled spec
  body is approximated by theming `textual`'s Markdown widget, not by a
  custom renderer.
- **Key map** (board): `q` quit, `/` search, `g` cycle grouping, `f` filter,
  `⏎` open detail, `^p` palette — plus the existing spec'd `r`/`l`/`o`
  card actions. (Modals): `⇥` next tab, `j`/`k` scroll, `o` open artifact in
  `$EDITOR` (suspend launch), `y` copy slug, `esc` close. The card-level `o`
  (resume session) and modal-level `o` (open file) live in different scopes
  and never collide.
- **Engine constraints hold**: `textual` remains the single third-party
  dependency, confined to `dashboard.py`/`tests_textual/`; the stdlib-only
  `tests/` suite keeps passing without it; every member change bumps the
  plugin version in its own PR.

## Design

The screen decomposes into five regions, and the member changes follow those
seams plus one cross-cutting foundation:

1. **Theme (foundation)** — the registered Shipd theme plus a restyle of the
   existing chrome to flat dark surfaces (no round borders, tinted lane
   header bands, accent focus states). Lands first; every later member
   references its variables.
2. **Lane content** — the row redesign: one-row issue rows (risk glyph +
   slug + live stage), one-row epic group headers (`▾ slug · initiative`,
   count, the existing inline run/open controls), per-lane empty-state
   texts. Generalizes the current `TaskCard`/`Collapsible` mount path.
3. **Header bar** — brand block, centered search input, the
   epic/initiative/none segmented control (replacing the checkbox strip),
   and the autopilot indicator. Introduces the three-state grouping mode.
4. **Search & filter strip** — the `/` search flow (live filtering, match
   highlighting, match count, clear) and the strip below the header: totals,
   removable filter chips (risk / epic / initiative), the `f` add-filter
   flow, synced-ago and shipped-this-week stats.
5. **Modal layer** — spec-detail, epic-detail, and run-confirm modals
   restyled to the mock: accent title bar with inline close, badge meta row,
   accent tab strip, per-modal footer key hints, epic member rows with lane
   badges, `y` copy and `o` open-in-editor.
6. **Command palette** — `^p` opens `textual`'s built-in palette populated
   with board commands (grouping modes, filter clearing, quit), themed to
   match.

Dependency order: theme → rows → header → {search, filters, modals,
palette}. Search depends on the header's input widget; the filter strip
depends on the header's counts plumbing; modals and palette are independent
after the theme lands.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| board-theme | Register the Shipd design-system palette as a custom textual theme and restyle existing chrome (lanes, cards, footer, focus states) to flat dark surfaces through its variables | medium | medium | low | medium |
| board-rows | One-row issue rows with risk-colored glyphs and live stage, one-row epic group headers with counts and inline controls, per-lane tinted headers and empty-state texts | medium | high | low | medium |
| board-header | Header bar with brand block, centered search input widget, epic/initiative/none segmented grouping control replacing the checkbox strip, and the heartbeat-derived autopilot indicator | medium | medium | low | medium |
| board-search | Live search: `/` focuses the input, lanes filter as you type with accent match highlighting and a match count, `esc`/`✕` clears | medium | medium | low | low |
| board-filters | Filter strip: spec/epic/initiative totals, removable risk/epic/initiative filter chips with an `f` add-filter flow, synced-ago and metrics-derived shipped-this-week stats | medium | medium | medium | medium |
| board-modals | Restyle the spec-detail, epic-detail, and run-confirm modals: accent title bars, badge meta rows, themed tab strip, footer key hints, lane badges on epic member rows, `y` copy slug and `o` open-in-editor | medium | medium | low | medium |
| board-palette | Populate and theme the built-in command palette (`^p`): grouping modes, filter clearing, and board actions as commands | low | low | low | low |
