# scrollbar-badge-polish
Status: verified

## Idea

Pin the board's scrollbars to the mock's muted border tones through the Shipd
theme and stop the spec-detail modal from rendering a `?` placeholder risk
chip for unrated members.

### Motivation

The TUI declares no scrollbar colors, so textual derives them from the theme's
`primary` — every scrollable surface grows a glowing acid-chartreuse thumb
(and solid-accent when active), while the "Shipd Board TUI" mock specifies a
subtle `#3E3E52` thumb on a `#1C1C26` track; separately, a member without a
risk rating (any standalone change) shows a cryptic muted `?` chip in its
spec-detail badge row. Both were spotted on the live board after the
`board-stall-buttons` merge.

### Details

- Add scrollbar overrides to `SHIPD_THEME.variables` so textual's derivation
  never runs: thumb `#3E3E52` (the existing border-strong tone), hover/active
  `#55556A`, track/corner `#1C1C26` — no new colors outside the theme
  definition.
- In `MemberDetailScreen.compose`, yield the risk badge only when the member
  carries a risk rating; an unrated member's badge row starts at the lane
  chip.

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- No per-widget scrollbar CSS — the theme variables are the single override
  point, and every scrollable surface inherits them.
- No change to `_risk_badge` itself: a present-but-unknown risk value still
  renders as a muted chip with its raw text; only the absent-risk case stops
  rendering.
- No change to the epic-detail or run-confirm modals' badge rows.

## Implementation

- **Scrollbars are themed, not widget-styled.** textual's `ColorSystem`
  computes `scrollbar` as `background-darken-1 + primary@0.4`,
  `scrollbar-active` as solid `primary`, and `scrollbar-background` as
  `background-darken-1` — but each is wrapped in a `get(name, default)` that
  prefers a same-named entry in the theme's `variables`. So add to
  `SHIPD_THEME.variables`:
  `scrollbar: #3E3E52`, `scrollbar-hover: #55556A`,
  `scrollbar-active: #55556A`, `scrollbar-background: #1C1C26`,
  `scrollbar-background-hover: #1C1C26`,
  `scrollbar-background-active: #1C1C26`,
  `scrollbar-corner-color: #1C1C26`.
  The hex values reuse the palette's existing border-strong / fg-subtle /
  panel tones, honoring the epic's "one registered theme is the palette's
  single source" decision. Rejected: `scrollbar-*` rules in widget CSS — it
  would need repeating on every scrollable widget and the theme override
  covers all of them at once.
- **Risk chip guard at the compose site.** In `MemberDetailScreen.compose`,
  wrap the existing `yield _risk_badge(m.get("risk"))` in
  `if m.get("risk"):` and update the badge-row comment; `_risk_badge` keeps
  its current signature and fallback (its `?` branch now only fires for a
  truthy non-vocabulary value, where the raw text renders muted). Rejected:
  returning `None` from `_risk_badge` — a conditional yield at the one call
  site is smaller than making every caller None-tolerant.
- **Tests** (`tests_textual/test_dashboard.py`, suite conventions):
  - Assert `app.get_css_variables()` resolves the seven scrollbar names to
    the pinned hex values (proving the derivation was overridden — the
    default would blend primary).
  - Mount a spec-detail modal for a member dict without a `risk` key and
    assert the badge row contains no `badge-risk-*` chip and no `?` static;
    the existing with-risk badge-row test stays as the positive case.
- **Risk:** future textual versions could rename the scrollbar variable
  names; the variables test pins today's contract so a rename fails loudly
  in `tests_textual`, not silently on screen.
- **Version bump** owed by the cache-snapshot rule:
  `plugins/s/.claude-plugin/plugin.json` to the next patch above the current
  `main` value at commit time (expected `0.6.58` → `0.6.59`).
