## 1. Dependency-free epic-artifact helper

- [x] 1.1 [req: board-epic-grouping] In `plugins/s/skills/build/tests/` (a NEW
      module, e.g. `test_epic_markdown.py`), add unit tests for a
      `dashboard.epic_markdown(root, slug)` helper: build a temp content dir with
      `epics/<slug>/epic.md` and assert the helper returns that file's text;
      assert it returns `None` for an unknown slug. MUST pass under system
      `python3` with `textual` NOT installed (same exec-and-swallow-ImportError
      loader as `tests/test_change_artifacts.py`). Run and observe failure.
- [x] 1.2 [req: board-epic-grouping] In `dashboard.py`, implement
      `epic_markdown(root, slug)` as a pure, stdlib-only module-level helper next
      to `change_artifacts`/`epic_is_runnable` (before the module's `textual`
      import): return the text of `<contentdir>/epics/<slug>/epic.md` (resolve via
      `sc.specs_dir(root)`; do NOT hardcode `.am`) or `None` when absent. Confirm
      1.1 passes and the dependency-free suite stays green.

## 2. Open control on every epic header

- [x] 2.1 [req: board-epic-grouping] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add tests: with grouping on, EVERY epic group header
      (both a runnable and a non-runnable epic) contains an open `Button`
      (`.epic-open-button`) distinct from the run button. Run and observe failure.
- [x] 2.2 [req: board-epic-grouping] In `dashboard.py` `_mount_epic_groups`, after
      the conditional run button, always append an open
      `Button("☰", id="open-epic-<lane>-<slug>", classes="epic-open-button")` to
      the group row, carrying a distinct marker attribute
      `open_button.epic_open_slug = group_slug` (NOT `epic_slug`). Keep it a
      sibling of the `Collapsible`. Confirm 2.1 passes.

## 3. Epic-detail modal

- [x] 3.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add
      tests: clicking an epic header's open button pushes an `EpicDetailScreen`
      and leaves the group's `collapsed` unchanged; the modal's rendered text
      names the epic slug and status and lists its member specs each with state
      and risk; a `Markdown` widget is present when the epic's `epics/<slug>/
      epic.md` exists (point `root` at a fixture/temp content dir that has one);
      clicking the `✕` close control dismisses the screen and pressing `Escape`
      also dismisses it. Run and observe failure.
- [x] 3.2 [req: board-epic-grouping] In `dashboard.py`, add
      `EpicDetailScreen(ModalScreen)` constructed with the epic slug: a centred
      `Container` (`width: 80%; height: 80%`) holding a header (`<slug>
      [<status>]` plus theme/initiative when set) with a top-right
      `Button("✕", id="epic-detail-close")`; a `Rule`; a member-specs list built
      from `_find_epic(self.app.board, slug)` (each member `<slug> [<risk>]
      <state>`, or a short notice when none); another `Rule`; and the overview
      from `epic_markdown(self.app.root, slug)` rendered as `Markdown` inside a
      `VerticalScroll` (or a not-found `Static` when `None`). Add an
      `escape`→dismiss binding and an `on_button_pressed` dismissing on
      `epic-detail-close`. Then branch `BoardApp.on_button_pressed`: a button with
      `epic_open_slug` → `push_screen(EpicDetailScreen(slug))` (checked first); a
      button with `epic_slug` → the existing `EpicRunConfirmScreen` path
      (unchanged). Confirm 3.1 passes.

## 4. Version bump & verification

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.34, so 0.6.35 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 4.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then, in a venv with `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual`; both green.
- [x] 4.3 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): confirm every epic header shows the ☰ open control; clicking it
      opens the epic-detail modal showing the epic status/theme/initiative, the
      member-spec list with states, and the epic.md rendered as Markdown; ✕ and
      Escape both close it; the run control still works and opening does not
      collapse the group.
