## 1. Runnable predicate (dependency-free)

- [x] 1.1 [req: board-epic-grouping] In `plugins/s/skills/build/tests/` (a NEW
      module, e.g. `test_epic_runnable.py`), add unit tests for a
      `dashboard.epic_is_runnable(epic)` helper covering: `ready` + an `unplanned`
      member → True; `active` + a `ready` member → True; `ready` with only
      `shipped`/`archived` members → False; `complete` (any members) → False;
      `active` with no members → False. These MUST pass under system `python3`
      with `textual` NOT installed. Run and observe failure.
- [x] 1.2 [req: board-epic-grouping] In `dashboard.py`, implement
      `epic_is_runnable(epic)` as a pure, stdlib-only module-level helper next to
      the other stdlib helpers (e.g. near `_find_epic`): return True iff
      `epic.get("status")` is `"ready"` or `"active"` AND any member's
      `state` is `"unplanned"` or `"ready"`. Confirm 1.1 passes and the
      dependency-free suite stays green.

## 2. Guard the run control

- [x] 2.1 [req: board-epic-grouping] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add tests: with grouping on, a runnable epic's group
      header contains a run `Button`, and a `complete` (or no-drivable-member)
      epic's group header contains no run `Button`. Run and observe failure.
- [x] 2.2 [req: board-epic-grouping] In `dashboard.py` `_mount_epic_groups`, only
      build and mount the `▶` run `Button` when
      `epic_is_runnable(_find_epic(self.board, group_slug))` is True; otherwise
      mount the group's `Collapsible` with no run button (collapse, visuals, and
      the group row otherwise unchanged). Confirm 2.1 passes.

## 3. Confirmation modal

- [x] 3.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add
      tests: clicking a runnable epic's run button pushes an
      `EpicRunConfirmScreen` and dispatches NO epic run yet (assert via the
      injectable launch/dispatch seam the existing epic-run tests use — zero
      launches) and leaves the group's `collapsed` unchanged; the modal shows the
      exact text "This will deliver the full epic, are you sure you want to
      continue?"; activating Yes dispatches exactly one epic-level run for that
      epic and dismisses the modal; activating No, the ✕ close control, or
      pressing `Escape` dismisses with zero dispatches. Run and observe failure.
- [x] 3.2 [req: board-epic-grouping] In `dashboard.py`, add
      `EpicRunConfirmScreen(ModalScreen)` constructed with the epic slug: a
      centred `Container` holding a top-left `Button("✕", id="epic-run-close")`, a
      `Static` with the exact prompt text, and `Yes` (`id="epic-run-yes"`) / `No`
      (`id="epic-run-no"`) buttons; an `escape`→dismiss binding; and
      `on_button_pressed` routing `epic-run-yes` →
      `self.app.dispatch_epic_run(self.epic_slug)` then `dismiss()`, and
      `epic-run-no`/`epic-run-close` → `dismiss()` only. Then change
      `BoardApp.on_button_pressed` so a run button (`epic_slug`-carrying) pushes
      `EpicRunConfirmScreen(slug)` instead of calling `dispatch_epic_run`
      directly. Add CSS to place the ✕ at the box's top-left. Confirm 3.1 passes.

## 4. Version bump & verification

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.33, so 0.6.34 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 4.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then, in a venv with `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual`; both green.
- [x] 4.3 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): confirm a `complete` epic's header shows no ▶; on a runnable
      epic, clicking ▶ opens the confirm modal (exact text, Yes/No, top-left ✕);
      No/✕/Escape close it with no run; Yes dispatches the epic run.
