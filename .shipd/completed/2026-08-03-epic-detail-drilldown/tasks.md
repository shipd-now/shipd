## 1. Clickable member rows in the epic-detail modal

- [x] 1.1 [req: board-epic-grouping] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add tests: open an epic's epic-detail modal (via its
      open control) for an epic with members; assert the listed member rows are
      the new clickable widget (e.g. `dashboard.EpicMemberRow`) and their
      **rendered** text (`str(row.render())`) still contains the risk in brackets
      (e.g. `[low]`) and the state. Then click one member row and assert a
      `dashboard.MemberDetailScreen` for that member's slug is pushed onto the
      screen stack **on top of** the `EpicDetailScreen` (the epic modal remains in
      the stack beneath), and that pressing `Escape` on the member modal returns
      to the `EpicDetailScreen`. Run and observe failure.
- [x] 1.2 [req: board-epic-grouping] In `dashboard.py`, add an
      `EpicMemberRow(Static)` widget (near `TaskCard`/`EpicDetailScreen`, inside
      the guarded `textual` block) constructed with `(epic_slug, member, entry,
      epic_status)`: label `"%s  [%s]  %s" % (slug, risk or "?", state or "?")`
      with `markup=False`, `can_focus = True`, and a `epic-member-row` class; an
      `on_click` that calls `self.app.push_screen(MemberDetailScreen(
      self.epic_slug, self.member, self.entry, self.epic_status))` (reusing the
      exact modal a `TaskCard` opens). Then in `EpicDetailScreen.compose`, replace
      the per-member `Static` with: resolve `roster = _roster_by_slug(epic.get(
      "heartbeat"))` once and yield `EpicMemberRow(self.epic_slug, member,
      roster.get(member["slug"], {}), epic.get("status"))` per member (keep the
      "no specs" notice for an empty list). Leave the rest of the modal unchanged.
      Confirm 1.1 passes.

## 2. Version bump & verification

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.35, so 0.6.36 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 2.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then, in a venv with `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual`; both green.
- [x] 2.3 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): open an epic-detail modal, confirm each member row shows its risk
      and state, click a member row and confirm its spec-detail modal opens on top,
      and Escape returns to the epic-detail modal (not straight to the board).
