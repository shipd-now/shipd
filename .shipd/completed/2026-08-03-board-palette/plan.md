# board-palette
Status: verified
Epic: update-ui-look-feel

## Idea

Populate the delivery board's built-in command palette (`^p`): board commands
— toggle grouping, clear search, quit — replace textual's stock system
commands, and the footer advertises the key.

### Motivation

The board's `^p` palette already opens (textual enables it by default) but
lists textual's stock demo commands — including a theme switcher that
contradicts the epic's one-registered-theme decision. The approved
`update-ui-look-feel` epic defines a palette populated with board commands
(grouping, filter clearing, quit) as part of the Shipd design, and
`board-palette` is the member that delivers it.

### Details

- Override `BoardApp.get_system_commands` to yield exactly the board's
  commands — no `super()` call, so the stock Theme/Keys/Screenshot commands
  disappear (ask-mikk oracle-settled; cited: epic/update-ui-look-feel).
- Commands on the board screen: **Group by epic** (toggles grouping through
  the existing checkbox path), **Clear search** (offered only while a query
  is active; runs the shared clear path), **Quit** (always).
- Opened over a modal screen, the palette offers only **Quit** — the board
  commands act on board-screen widgets a modal cannot reach.
- A visible `ctrl+p` binding (key display `^p`, per the epic's key map) joins
  `BoardApp.BINDINGS` so the footer advertises the palette; textual skips its
  hidden default when the app binds `command_palette` itself.
- No palette CSS and no hex: the built-in palette styles through theme
  variables, so it adopts the Shipd theme when `board-theme` registers it.

Affected capability: `delivery-dashboard` (one added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, and the plugin
version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No three-state grouping cycling — `board-header` introduces the
  `epic`/`initiative`/`none` mode and its delta amends the palette's grouping
  command then (the epic's amendments-travel-with-the-member rule).
- No filter-chip clearing — `board-filters` owns chips; today "filter
  clearing" is the live-search clear from `board-search`.
- No custom command `Provider`, fuzzy sources, or extra board actions beyond
  the epic Design's closed list (grouping, filter clearing, quit).
- No Shipd theme registration or palette-specific styling — `board-theme`
  owns the theme; this change hard-codes no colors.
- No changes to `build_board` aggregation, the pure launch builders, or the
  heartbeat format.

## Implementation

- **Population hook: `get_system_commands`, not a custom provider.**
  `App.COMMANDS` already carries the system-commands provider in the pinned
  textual (8.2.8), and `get_system_commands(screen)` is its documented
  override point, yielding `SystemCommand(title, help, callback)` tuples
  (import `SystemCommand` from `textual.app`). Rejected: a custom `Provider`
  class in `COMMANDS` — extra machinery for a fixed command list.
- **Replace, not extend (oracle-settled).** The override does not call
  `super()`: the stock "Theme" command would hand the user a switch that
  breaks the epic's "one registered theme" decision, and Keys/Screenshot read
  as demo chrome against the epic's product bar. Quit is re-yielded through
  `self.action_quit` so the palette keeps an exit affordance.
- **Command wiring reuses existing paths.** "Group by epic" calls
  `self.action_toggle_grouping` — routing through the checkbox so the control
  stays in sync and `on_checkbox_changed` repaints, exactly like the `g` key.
  "Clear search" uses the async `self._clear_search` (textual accepts async
  command callbacks), the same path as `escape`/`✕`. Neither touches
  aggregation.
- **Conditional yield mirrors textual's own pattern.** "Clear search" is
  yielded only while `self.search_query` is non-empty (the palette re-queries
  commands on every open, so the set stays current). Board commands as a
  whole are yielded only when the `screen` argument is the app's base board
  screen (`screen is self.screen_stack[0]`); from a modal screen only Quit is
  yielded — `action_toggle_grouping`'s `query_one` would fail against a modal
  screen. Rejected: making callbacks modal-safe — hiding inapplicable
  commands is simpler and reads better than commands that no-op.
- **Footer visibility.** Add `Binding("ctrl+p", "command_palette", "Palette",
  key_display="^p", priority=True)` to `BoardApp.BINDINGS`. The pinned
  textual's `App.__init__` skips its hidden default binding when the app
  already binds `command_palette`, so this is the supported override;
  `priority=True` matches the default so `^p` still fires while the search
  input holds focus.
- **Tests** go to `tests_textual/test_dashboard.py`, pilot-driven like the
  board-search suite: `ctrl+p` pushes a `textual.command.CommandPalette`
  screen; the command set is asserted by calling `get_system_commands`
  directly with the board screen (and a modal screen) and comparing titles;
  callback effects are asserted by invoking the yielded callbacks. The
  stdlib-only `tests/` suite is untouched — everything lands in
  `dashboard.py`, which already requires `textual`.

Risk: minimal — view-level only, no data-layer change. The main forward
coupling is the grouping command's phrasing; the three-state amendment is
explicitly parked on `board-header`, which owns that delta per the epic.
