## 1. Stage-aware notice

- [x] 1.1 [req: modal-live-artifacts] In
      `plugins/s/skills/build/tests/test_change_artifacts.py`, add failing
      tests for a pure `artifact_notice(entry)` helper, loaded through the
      file's existing `_load_dashboard_stdlib()` loader (the helper will live
      in `dashboard.py`'s pre-textual stdlib zone, next to
      `change_artifacts`). Assert: stage `plan` attempt 1 →
      `plan in progress (plan#1) — spec files appear once emitted`; stage
      `plan` without attempt → `plan in progress (plan) — spec files appear
      once emitted`; no stage (or empty entry) →
      `not yet planned — no spec files`.
- [x] 1.2 [req: modal-live-artifacts] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement
      `artifact_notice(entry)` and use it for the notice widget (id
      `#artifact-notice`) in `MemberDetailScreen.compose`; confirm the 1.1
      tests pass.

## 2. Live artifact mount

- [x] 2.1 [req: modal-live-artifacts] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: a modal open on a no-artifact member shows the stage-aware
      notice; after writing `planned/<slug>/plan.md` + `tasks.md` to the
      member's location fixture, invoking the screen's refresh handler
      replaces the notice with the Plan/Tasks tabs on the same screen object;
      a further refresh leaves the mounted `TabbedContent` widget identity
      unchanged (no remount).
- [x] 2.2 [req: modal-live-artifacts] In
      `plugins/s/skills/build/scripts/dashboard.py`, start the modal's
      3-second interval unconditionally and extend its refresh handler:
      while `#artifact-notice` is mounted, re-run the artifact resolution
      and, on a non-empty result, remove the notice and mount the tabbed
      artifact view in its place; never touch already-mounted tabs. Confirm
      the 2.1 tests pass.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
