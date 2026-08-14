## 1. Worktree-aware artifact resolution

- [x] 1.1 [req: modal-worktree-artifacts] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: a `MemberDetailScreen` for a member whose `location` points at a
      fixture worktree directory holding `planned/<slug>/plan.md`, a spec, and
      `tasks.md` (while the app root has none) renders the Plan/Spec/Tasks
      tabs; a member with a `location` that holds no change shows the
      not-yet-planned notice without error; a root-planned member renders
      exactly as before.
- [x] 1.2 [req: modal-worktree-artifacts] In
      `plugins/s/skills/build/scripts/dashboard.py`, resolve the modal's
      artifacts via `change_artifacts(self.member.get("location") or
      self.app.root, ...)` in `MemberDetailScreen.compose`; confirm the 1.1
      tests pass.

## 2. Ship

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 2.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
