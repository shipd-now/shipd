## 1. Dependency-free artifact locator

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests/` (a NEW test module,
      e.g. `test_change_artifacts.py`), add unit tests for a
      `dashboard.change_artifacts(root, slug)` helper: build a temp content dir
      with `planned/<slug>/` and `completed/<date>-<slug>/` each holding
      `plan.md`, `specs/<cap>/spec.md`, `tasks.md`; assert the helper returns an
      ordered list of `{label, path, text}` (Plan, Spec: <cap>, Tasks), prefers
      `planned/` over `completed/`, includes only files that exist, and returns
      `[]` for an unknown slug. These tests MUST run under system `python3` with
      `textual` NOT installed. Run and observe failure.
- [x] 1.2 [req: board-tui] In `dashboard.py`, implement `change_artifacts(root,
      slug)` as a module-level, stdlib-only helper (os/glob/file reads; no
      `textual`) next to the other stdlib helpers. Resolve the change dir under
      the content dir (`sc.specs_dir(root)` / existing content-dir resolution — do
      NOT hardcode `.am`): prefer `planned/<slug>/`, else the newest
      `completed/*-<slug>/`. Return the ordered `{label, path, text}` list
      described in 1.1, or `[]`. Confirm 1.1 passes and the full dependency-free
      suite still passes.

## 2. Thread the epic status to the card

- [x] 2.1 [req: board-tui] In `dashboard.py`, add an `epic_status` parameter to
      `TaskCard.__init__` (store `self.epic_status`), and pass it at both
      construction sites — the non-shipped branch of `_render_lanes` and
      `_mount_shipped_group` (both already have the epic `status` in scope from
      `_lane_contents`). Keep existing card behavior otherwise.

## 3. Rebuild the spec-detail modal

- [x] 3.1 [req: board-tui] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add tests (mounting the real app, or pointing `root` at
      a populated temp content dir) asserting the opened `MemberDetailScreen`:
      (a) its container is larger than the previous fixed 60-wide box (e.g. its
      rendered/region width exceeds 60 or its styles width is the new value);
      (b) the header text names the change slug and `epic: <slug> [<status>]`;
      (c) for a change WITH artifacts, a `TabbedContent` is present with the
      expected tab labels (Plan / Spec* / Tasks); (d) for an unplanned change
      (no dir), NO `TabbedContent` is present and a not-yet-planned notice shows;
      (e) clicking the `✕` close control dismisses the screen (screen stack
      returns to the board). Run and observe failure.
- [x] 3.2 [req: board-tui] In `dashboard.py`, import the needed widgets
      (`TabbedContent`, `TabPane`, `Markdown`, `Rule`, `Button`) inside the
      guarded `textual` import block, and rebuild `MemberDetailScreen`: accept
      `epic_status`; CSS container `width: 80%; height: 80%`; a header region with
      `slug [risk · state]` and `epic: <slug> [<status>]`; a clickable `✕` close
      control (`Button` id `close-detail` → `dismiss`, keeping the `Escape`
      binding); a horizontal `Rule`; and a body built from
      `change_artifacts(self.app.root, member["slug"])` — a `TabbedContent` of
      `TabPane(label, VerticalScroll(Markdown(text)))` per artifact, or a single
      not-yet-planned `Static` when the list is empty. Update
      `TaskCard.action_select` to pass `epic_status` into the screen. Leave the
      `Enter`/click open paths otherwise unchanged. Confirm 3.1 passes.

## 4. Version bump & verification

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.31, so 0.6.32 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 4.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed —
      this includes the new locator tests), then, in a venv with `pip install -r
      requirements.txt`, run `plugins/s/skills/build/tests_textual`; both green.
- [x] 4.3 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): open a card whose change has artifacts on disk and confirm the
      large modal shows the epic reference, a rule, and a tabset switching between
      Plan / Spec / Tasks; click `✕` to close. Also open an unplanned card and
      confirm the not-yet-planned notice.
