# tab-focus-contrast
Status: verified

## Idea

Make the spec-detail modal's active artifact tab readable when the tab strip
has focus by rendering it as a solid accent block with dark bold text.

### Motivation

Clicking an artifact tab focuses textual's `Tabs` widget, whose stock
`Tabs:focus .-active` rule paints the active tab with
`$block-cursor-background` (the theme's chartreuse primary) under
`$block-cursor-foreground` (the near-white text tone) — pale-on-chartreuse,
unreadable. The user reported it and chose dark-on-accent as the fix
direction, which matches how the active grouping mode and primary buttons
already read.

### Details

- One app-wide rule in `BoardApp.CSS`: while a `Tabs` widget has focus, its
  active `Tab` renders `$background` text on solid `$accent`, bold —
  out-specifying textual's stock focus rule. Covers the member modal's strip
  and any future tab strip on the board.

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- No change to the unfocused tab styling (accent text, muted inactive tabs,
  accent underline) — only the focused-active state changes.
- No theme-level `block-cursor-*` override: those variables also drive
  OptionList/DataTable cursors (e.g. the command palette), which are out of
  scope and unaudited here.

## Implementation

- **The defect is textual's stock rule**, verified in the pinned textual
  8.2.8 (`widgets/_tabs.py` DEFAULT_CSS):
  `Tabs:focus { & .-active { text-style: $block-cursor-text-style; color:
  $block-cursor-foreground; background: $block-cursor-background; } }` —
  with the shipd theme both cursor tones are light, so contrast collapses.
- **Fix via a more specific app-wide selector**, added to `BoardApp.CSS`:

  ```
  Tabs:focus Tab.-active {
      color: $background;
      background: $accent;
      text-style: bold;
  }
  ```

  `Tab.-active` (type + class) out-specifies the stock `.-active`
  (class only) under the same `Tabs:focus` ancestor, so no `!important`-style
  hacks are needed. App CSS applies across every screen, so the member
  modal's strip inherits it and any future tab strip gets it for free.
  Rejected: overriding `block-cursor-foreground`/`block-cursor-background`
  in `SHIPD_THEME.variables` — those tokens also style OptionList and
  DataTable cursors (command palette included), a wider blast radius than
  this fix needs. Rejected: keeping the unfocused look on focus
  (transparent background) — focus should read *stronger*, and dark-on-solid
  -accent is the established emphasis idiom (mode-active, button-primary);
  the user explicitly offered this direction.
- **Tests** (`tests_textual/test_dashboard.py`, suite conventions): in the
  mounted member-detail modal, focus the `Tabs` widget (`app.set_focus` or
  clicking a tab), then assert the active `Tab`'s resolved
  `styles.background` equals the theme accent at full alpha and
  `styles.color` equals the theme background (via `app.get_css_variables()`
  + `Color.parse`), with bold text; and assert the unfocused state still
  renders the accent-colored text on a non-accent background (the existing
  themed-tab test remains the unfocused case).
- **Version bump** owed by the cache-snapshot rule:
  `plugins/s/.claude-plugin/plugin.json` to the next patch above `main` at
  commit time (expected `0.6.60` → `0.6.61`).
