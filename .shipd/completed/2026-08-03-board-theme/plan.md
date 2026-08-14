# board-theme
Status: verified
Epic: update-ui-look-feel

## Idea

Register the Shipd design-system palette as a custom `textual` theme (`shipd`)
on the delivery board and restyle the existing chrome — lanes, cards, epic
group rows, modal borders, focus states — to flat dark surfaces referenced
only through theme variables.

### Motivation

The `tui` board renders in `textual`'s stock theme — round borders, default
palette, one literal `solid black` divider — and looks like a demo rather than
the Shipd design language the update-ui-look-feel epic adopted. This is the
epic's foundation member: it lands the palette as one registered theme so every
later member (rows, header, filters, modals, palette) references its variables
instead of scattering hex values.

### Details

- Define a module-level `SHIPD_THEME` in `dashboard.py` from the Shipd tokens
  (`~/projects/shipd-now/docs/shipd-now-design-system/project/colors_and_type.css`),
  exposing lane, risk, border, foreground-tier, and hover/active surfaces as
  named theme variables; register and activate it in `BoardApp.__init__`.
- Restyle the widget CSS through those variables: flat lane borders on dark
  surfaces, theme-border group separators (replacing `solid black`), risk bars
  re-pointed at the epic's risk mapping, accent-derived focus states, flat
  (non-round) modal borders.
- Amend the `delivery-dashboard` spec: ADD a Board theme requirement; MODIFY
  `board-epic-grouping`'s gray/black group visual to theme-variable surfaces.
- Bump the plugin version 0.6.42 → 0.6.43 (0.6.42 was taken by board-palette,
  which merged while this change was planned).

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies (`textual` 8.2.8
already carries the `Theme` API — verified against the pinned venv).

### Non-goals

- No row redesign, tinted per-lane header bands, or empty-state texts
  (board-rows); no header bar or grouping control (board-header); no filter
  strip (board-filters); no modal restructuring — accent title bars, tab
  strips, key hints (board-modals); no command palette (board-palette).
- No `html` verb changes: `_HTML_CSS` keeps its own inline page palette and is
  exempt from the no-hard-coded-colors rule.
- No data-layer, aggregation, or key-binding changes; no font management.

## Implementation

- **Theme lives in `dashboard.py`, module-level, beside the widget classes.**
  `from textual.theme import Theme`; `SHIPD_THEME = Theme(name="shipd",
  primary="#C6FF4E", secondary="#4DA6FF", accent="#C6FF4E",
  foreground="#F0F0F8", background="#0A0A0D", surface="#111118",
  panel="#1C1C26", success="#3DCC8E", warning="#FF8C42", error="#FF4D3D",
  dark=True, variables={...})`. Rejected: a separate theme module — the
  constitution confines `textual` imports to `dashboard.py`.
- **Variables dict** (the single place these hexes appear):
  `lane-unplanned #8888A0`, `lane-ready #4DA6FF`, `lane-building #FF8C42`,
  `lane-review #9B7FFF`, `lane-shipped #3DCC8E`; `risk-high #FF8C42`,
  `risk-medium #C6FF4E`, `risk-low #55556A`; `shipd-border #2A2A38`,
  `shipd-border-strong #3E3E52`; `bg-hover #22222E`, `bg-active #28283A`;
  `accent-dim #8FBF1A`; `fg-muted #8888A0`, `fg-subtle #55556A`. Non-standard
  tokens carry the `shipd-` prefix where a bare name (`border`) could shadow a
  builtin; lane/risk names are collision-free. Later members reference these
  as `$lane-*` / `$risk-*` — the epic's "single palette source" decision.
- **Registration in `BoardApp.__init__`** — `self.register_theme(SHIPD_THEME)`
  then `self.theme = "shipd"` right after `super().__init__()`, so the theme
  is active before first paint and under `run_test`. Verified working on
  textual 8.2.8 with custom variables resolving in widget CSS. Rejected:
  `on_mount` — a first frame could flash the default theme.
- **CSS restyle, all through variables:**
  - `Lane`: `border: round $primary` → `border: solid $shipd-border;
    background: $surface; border-title-color: $fg-muted;` (an unset title
    color would sink into the dark border tone).
  - `.epic-group-row`: `border-bottom: solid black` → `solid $shipd-border`.
    `.epic-group` keeps `background: $panel` (now the elevated `#1C1C26`).
  - `TaskCard` risk classes: `risk-low` `thick $success` → `thick $risk-low`,
    `risk-medium` `$warning` → `$risk-medium`, `risk-high` `$error` →
    `$risk-high` (the epic's risk-is-priority mapping: high=orange,
    medium=chartreuse, low=dim). Default card bar stays `thick $accent`.
  - Focus: `TaskCard:focus` → `background: $accent 15%` (accent-subtle) and
    drop its `border-left: thick $warning` override so the risk bar survives
    focus; `.epic-member-row:focus` likewise `$accent 15%`.
  - The three modal `CSS` blocks: `border: round $primary` → `border: solid
    $shipd-border-strong` — borders only; modal structure is board-modals'.
- **Structural no-hard-coded-colors test** — regex-scan the four CSS class
  attributes (`BoardApp`, `MemberDetailScreen`, `EpicRunConfirmScreen`,
  `EpicDetailScreen`) for hex literals, the word `black`/`white`, and `round`
  borders; plus exact-value assertions on `SHIPD_THEME.variables`. This pins
  the "single palette source" rule without brittle screenshot assertions.
- **Spec surface**: existing scenarios keep passing — `board-tui`'s "bordered
  lanes" and focus-highlight scenarios don't pin colors; only
  `board-epic-grouping`'s gray/black scenario changes wording, and its
  existing test (`test_group_headers_carry_grouping_class_no_status_colour`)
  asserts classes, not colors, so it stands unchanged.
- **Risk**: a future `textual` minor could add builtin variables colliding
  with the custom names; the pin `textual>=8.2.8,<9` plus the `shipd-`/`lane-`/
  `risk-` prefixes bound that. Terminals without truecolor downsample the
  palette — acceptable; `textual` handles quantization.
