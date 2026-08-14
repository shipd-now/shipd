## 1. Command palette population

- [x] 1.1 [req: board-command-palette] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      pilot-driven test class against the existing two-epic fixture board
      covering: pressing `ctrl+p` pushes a `textual.command.CommandPalette`
      screen; `list(app.get_system_commands(<board screen>))` with no active
      query yields titles for the grouping command and Quit only — no
      Theme/Keys/Screenshot titles; with `app.search_query` non-empty the
      clear-search command's title appears, and disappears after clearing;
      calling `list(app.get_system_commands(<a ModalScreen instance>))`
      yields only Quit; invoking the grouping command's callback (then
      `await pilot.pause()`) flips `app.group_by_epic`; with an active query
      filtering the board, awaiting the clear-search command's callback
      clears `app.search_query` and remounts every member's card; and
      `BoardApp.BINDINGS` carries a visible (`show` true) `ctrl+p` binding
      for `command_palette` with `key_display` `^p`. Run the class and
      observe it fail.
- [x] 1.2 [req: board-command-palette] In
      `plugins/s/skills/build/scripts/dashboard.py`, add
      `Binding("ctrl+p", "command_palette", "Palette", key_display="^p",
      priority=True)` to `BoardApp.BINDINGS`, and extend the existing
      `from textual.app import ...` import with `SystemCommand`.
- [x] 1.3 [req: board-command-palette] In `dashboard.py`, implement
      `BoardApp.get_system_commands(self, screen)` (no `super()` call): when
      `screen is self.screen_stack[0]`, yield `SystemCommand("Group by
      epic", "Toggle grouping the lanes' cards under epic headers",
      self.action_toggle_grouping)`, then — only while `self.search_query`
      is non-empty — `SystemCommand("Clear search", "Clear the live search
      and restore the full board", self._clear_search)`; in every case yield
      `SystemCommand("Quit", "Quit the delivery board", self.action_quit)`.
      Confirm every 1.1 test passes.

## 2. Verify and ship

- [x] 2.1 [req: *] Run the full textual suite (`python3 -m unittest discover
      -s plugins/s/skills/build/tests_textual`) and the stdlib suite
      without `textual` (`python3 -m unittest discover -s
      plugins/s/skills/build/tests`); both must pass — the stdlib suite
      unmodified.
- [x] 2.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.41 to 0.6.42.
