# board-modals tasks

## 1. Editor launch builder

- [x] 1.1 [req: board-modal-chrome] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, next to the
      existing launch-builder tests (`test_plan_without_tmux_suspends_in_worktree`),
      add tests asserting `dashboard.build_editor_launch("/x/plan.md")` returns
      `{"mode": "suspend", "argv": ["nano", "/x/plan.md"], "cwd": "/x"}` with
      `EDITOR=nano` patched into the environment, returns `argv: ["vi", ...]`
      with `EDITOR` unset, and honors an explicit `editor=` argument. Run them
      and observe them fail — the builder does not exist yet.
- [x] 1.2 [req: board-modal-chrome] In
      `plugins/s/skills/build/scripts/dashboard.py`, add
      `build_editor_launch(path, editor=None)` beside `build_open_launch`:
      resolve the editor from the argument, else `os.environ.get("EDITOR")`,
      else `"vi"`, and return `{"mode": "suspend", "argv": [editor, path],
      "cwd": os.path.dirname(path)}`. Confirm the 1.1 tests pass.

## 2. Title bars, badges, tab strip, footer hints

- [x] 2.1 [req: board-modal-chrome, board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add
      structural tests (following the
      existing modal-test patterns): each of `MemberDetailScreen`,
      `EpicDetailScreen`, and `EpicRunConfirmScreen` mounts a
      `.modal-title-bar` row containing its `✕` close button; the spec-detail
      modal mounts a badge row with `badge-risk-*` and `badge-lane-*` chips
      plus a muted stage chip while driving; the epic-detail modal mounts
      status/theme/initiative chips; every `EpicMemberRow` carries a
      `badge-lane-*` element matching `dashboard._member_column` for that
      member; each modal mounts a `.modal-footer-hints` line with its exact
      hint string (spec-detail `⇥ tabs · j/k scroll · o editor · y copy · esc
      close`, epic-detail `j/k scroll · o editor · y copy · esc close`,
      run-confirm `esc close`); and the three modal CSS blocks style
      `.modal-title-bar` with `background: $accent`. Run them and observe
      them fail.
- [x] 2.2 [req: board-modal-chrome] In `dashboard.py`, restyle
      `MemberDetailScreen.compose`: convert the header `Horizontal` to the
      accent `.modal-title-bar` (slug title `width: 1fr`, existing `✕`
      inline), add the badge meta row (`badge-risk-<risk>` chip,
      `badge-lane-<lane>` chip via `_member_column`, muted stage chip while
      driving, muted `epic: <slug> [<status>]` chip), keep session/actions as
      muted lines and everything below the `Rule` unchanged, and dock the
      `.modal-footer-hints` line at the container bottom. Add the CSS for the
      title bar, chips, and hints using only `$` theme variables.
- [x] 2.3 [req: board-modal-chrome] In `dashboard.py`, restyle
      `EpicDetailScreen.compose` the same way: accent title bar naming the
      epic slug, badge row with the status chip plus theme/initiative chips
      when set, and the footer hint line; extend `EpicMemberRow` to render a
      `badge-lane-<lane>` element derived via `_member_column(member, entry)`
      ahead of its `<slug>  [<risk>]  <state>` text. Leave the stall banner,
      member-click push, and overview Markdown untouched.
- [x] 2.4 [req: board-epic-grouping, board-modal-chrome] In `dashboard.py`,
      restyle `EpicRunConfirmScreen`: replace the top-left `✕` row with the
      accent `.modal-title-bar` naming the epic slug and carrying the `✕`
      inline at its right edge, keep the exact prompt text and Yes/No
      controls and their dispatch semantics, and add the `esc close` footer
      hint line. Update the class docstring (it documents the top-left `✕`
      contrast).
- [x] 2.5 [req: board-modal-chrome] In `dashboard.py`, theme the spec-detail
      artifact tab strip: `MemberDetailScreen` CSS for `Tab`/active-tab
      states coloring the active tab and underline with `$accent` and
      inactive tabs with `$fg-muted`. Confirm all 2.1 tests and the existing
      CSS hygiene test pass.

## 3. Modal keys

- [x] 3.1 [req: board-modal-chrome] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add key
      tests: `y` in the spec-detail (and epic-detail) modal calls
      `copy_to_clipboard` with the member (epic) slug (patch the method);
      `Tab` in a spec-detail modal with Plan/Spec/Tasks tabs advances the
      active tab and wraps; `j` then `k` scrolls the active pane down then
      back; `o` in a spec-detail modal with tabs calls `_spawn_launch`
      (patched) with the editor launch for the active tab's `path`; `o` in
      epic-detail spawns the launch for `epics/<slug>/epic.md`; `o` while the
      not-yet-planned notice shows spawns nothing and leaves the modal open.
      Run them and observe them fail.
- [x] 3.2 [req: board-modal-chrome] In `dashboard.py`, add
      `MemberDetailScreen` bindings and actions: `tab` → activate the next
      artifact tab wrapping (no-op while the notice shows), `j`/`k` → scroll
      the active tab pane's `VerticalScroll` down/up, `y` →
      `self.app.copy_to_clipboard(member slug)`, `o` → build the editor
      launch for the active tab's artifact `path` via `build_editor_launch`
      and hand it to `self.app._spawn_launch` (no-op without artifacts; keep
      the artifact list from `compose`/the live swap on the instance so the
      action can resolve the active tab's path).
- [x] 3.3 [req: board-modal-chrome] In `dashboard.py`, add
      `EpicDetailScreen` bindings and actions: `j`/`k` → scroll the overview
      `VerticalScroll`, `y` → copy the epic slug, `o` → editor launch for
      `<content-dir>/epics/<slug>/epic.md` when it exists (resolve the path
      with the same `spec_common` content-dir resolution `epic_markdown`
      uses), else no-op. Confirm the 3.1 tests pass.

## 4. Verify and ship

- [x] 4.1 [req: *] Run the full `textual` suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests_textual`)
      and the stdlib-only suite without `textual`
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`);
      both must pass.
- [x] 4.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
