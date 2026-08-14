## 1. Click-to-open on the task card

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add a `Pilot` test to `AppMountTest`: mount the app,
      pick a `TaskCard` that is not currently focused, click it with
      `await pilot.click(<that card>)`, and assert (a) the top of the screen
      stack is a `dashboard.MemberDetailScreen` for that card's member (its
      `member["slug"]` matches) and (b) the clicked card now has focus
      (`card.has_focus`). Run it and observe failure.
- [x] 1.2 [req: board-tui] In `dashboard.py`, add an `on_click(self, event)`
      handler to `TaskCard` that calls `self.focus()` then `self.action_select()`
      (reusing the existing modal-push path — do not duplicate the
      `push_screen`). Import the `textual.events` / `Click` symbol you reference
      alongside the other guarded `textual` imports so the module still loads
      without `textual`. Leave `action_select`, the `Enter`/`Escape` bindings,
      the `r`/`l`/`o` actions, and `MemberDetailScreen` unchanged. Confirm 1.1
      passes.

## 2. Version bump & verification

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.30, so 0.6.31 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 2.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then, in a venv with `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual`; both green.
- [x] 2.3 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): click a task-card and confirm a `MemberDetailScreen` is pushed
      and the card is focused, then dismiss with `Escape`.
