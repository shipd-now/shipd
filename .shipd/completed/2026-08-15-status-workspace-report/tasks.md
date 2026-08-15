## 1. Relocate standalone discovery

- [x] 1.1 [req: workspace-board-report] In
      `plugins/s/skills/build/tests/test_change_artifacts.py`, add a failing
      assertion to the existing `standalone_changes` test class: the
      function is importable as `spec_status.standalone_changes` and
      `dashboard.standalone_changes` delegates to it (e.g. monkeypatch
      `spec_status.standalone_changes` to a sentinel-returning stub and
      assert `dashboard.standalone_changes(root, set())` returns the
      sentinel). Run it and observe the failure.
- [x] 1.2 [req: workspace-board-report] Move `_standalone_plan_path`
      (dashboard.py:152) and `standalone_changes` (dashboard.py:169)
      verbatim into `plugins/s/skills/build/scripts/spec_status.py`
      (rewriting their `ss.`/module-local references), and replace the
      dashboard.py originals with thin delegating wrappers keeping the same
      names and signatures. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it passes, including the pre-existing standalone tests.

## 2. Workspace board report

- [x] 2.1 [req: workspace-board-report, status-cli] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests
      driving `show` with no argument and no selection: the
      `N specs · N epics · N initiatives` totals line (specs = members
      across epics, standalone excluded from the count); `shipped <n>/<m>`
      over members plus standalone rows; all four `<LANE> (<count>)`
      headers in board order including `(0)`; a non-shipped member row
      carrying epic slug, member slug, state, `risk <value>` (`?` when the
      stub row has no rating cells), and `[worktree]` for a
      worktree-derived state; a standalone change's row under epic column
      `standalone` with `risk ?`; `SHIPPED` holding only
      `<epic-slug> (<n>)` rollup rows plus `standalone (<n>)` when an
      archived standalone exists; a selection winning over the fallback;
      and bare `status` (no argument, no selection) still exiting non-zero
      with the no-selection error. Run them and observe the failure.
- [x] 2.2 [req: workspace-board-report] In
      `plugins/s/skills/build/scripts/spec_status.py`, implement
      `_workspace_report_lines(root)` per the plan's layout: epics from
      sorted `epics/*/epic.md` globs (skipping unreadable files), members
      via `sc.parse_epic_changes` + `_member_state_with_root` +
      `board_lane`, standalone entries via the relocated
      `standalone_changes(root, <all epic member slugs>)` (their
      `[worktree]` marker from `location` differing from the invocation
      root), row format `  %-20s %-22s %-12s risk %s%s`, shipped lane as
      per-epic rollups.
- [x] 2.3 [req: status-cli] In `cmd_show` (spec_status.py:398), before
      `_resolve_change`, print `_workspace_report_lines(root)` and return 0
      when no change is given and `read_current(root)` is None; leave
      `cmd_status` and every other verb untouched. Confirm 2.1's tests
      pass.
- [x] 2.4 [req: workspace-board-report] Update the usage banner and the
      argparse help for `show` in `spec_status.py` to name the no-argument
      workspace report.

## 3. Skill wrapper and plugin snapshot

- [x] 3.1 [req: interactive-status-skill] In
      `plugins/s/skills/status/SKILL.md`, change the no-argument mapping:
      `/s:status` runs `show` alone and relays its output (change one-liner
      when a selection exists, else the workspace board report, relayed
      verbatim); the paired bare-`status` call runs only when an argument
      is given or a selection exists. Document the workspace report
      briefly alongside the existing epic section.
- [x] 3.2 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` (patch bump).
- [x] 3.3 [req: *] Run the full suite
      `python3 -m unittest discover -s plugins/s/skills/build/tests`
      without `textual` installed and confirm everything passes.
