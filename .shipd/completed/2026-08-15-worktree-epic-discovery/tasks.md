## 1. Discovery seam (spec_status.py)

- [x] 1.1 [req: epic-status-verbs] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: `_epic_hosting_root`
      returns the invocation root when it hosts the epic, the sorted-first
      hosting worktree when only worktrees host it, and `None` when none does,
      skipping a worktree whose config is unreadable;
      `all_epic_slugs_with_roots` lists the root's epics (sorted) before
      worktree-only epics (sorted), the root winning a duplicated slug.
- [x] 1.2 [req: epic-status-verbs] Implement `_epic_hosting_root(root, slug)`
      and `all_epic_slugs_with_roots(root)` in
      `plugins/s/skills/build/scripts/spec_status.py` beside
      `_member_state_with_root`, using per-candidate `sc.specs_dir` resolution
      with `sc.ConfigError` skip; run the 1.1 tests green.

## 2. Status CLI read surfaces

- [x] 2.1 [req: status-cli] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: `status <slug>` and
      `show <slug>` fall back to an epic hosted only under a worktree; a name
      in no candidate still prints `?`.
- [x] 2.2 [req: status-cli] Route `_epic_fallback`, `cmd_status`, and
      `cmd_show`'s epic fallback in `spec_status.py` through
      `_epic_hosting_root`; run the 2.1 tests green.
- [x] 2.3 [req: epic-status-verbs] Add failing tests: `epic-show` on a
      worktree-only epic prints the board-shaped report with a
      `worktree: <name>` line directly after the metadata lines and none for a
      root-hosted epic; `epic-set-status ready <slug>` for a worktree-only
      epic exits non-zero with the epic-not-found error.
- [x] 2.4 [req: epic-status-verbs] Make `_epic_report_lines`/`cmd_epic_show`
      in `spec_status.py` resolve the epic via `_epic_hosting_root`, read file
      and status from the hosting root, and emit the `worktree: <name>` line;
      leave `cmd_epic_sync`/`cmd_epic_set_status` on the invocation root; run
      the 2.3 tests green.
- [x] 2.5 [req: workspace-board-report] Add failing tests: the bare-`show`
      workspace report counts a worktree-only epic in the totals line and
      renders its member rows under their lanes.
- [x] 2.6 [req: workspace-board-report] Make `_workspace_epic_slugs` return
      the discovery map from `all_epic_slugs_with_roots` and
      `_workspace_report_lines` read each epic from its hosting root; run the
      2.5 tests green.

## 3. Board aggregation (dashboard.py)

- [x] 3.1 [req: board-aggregation] Add failing tests to
      `plugins/s/skills/build/tests_textual/test_dashboard.py`: `build_board`
      aggregates a worktree-only epic with `location` set to the worktree
      root; a slug hosted in both root and worktree aggregates once from the
      root; `_all_epic_member_slugs` includes the worktree epic's stub
      members.
- [x] 3.2 [req: board-aggregation] Update `_epic_slugs`/`_epic_board`/
      `_all_epic_member_slugs`/`build_board` in
      `plugins/s/skills/build/scripts/dashboard.py` to consume
      `ss.all_epic_slugs_with_roots`, attach `location`, and read the epic
      file, `read_epic_status`, heartbeat, and run report from the hosting
      root; run the 3.1 tests green.
- [x] 3.3 [req: board-aggregation] Add failing tests: the text board
      (`board` verb) marks a worktree-hosted epic's header `[worktree]`; the
      TUI epic group header carries the marker; the epic-detail overview
      renders the worktree-hosted epic's markdown.
- [x] 3.4 [req: board-aggregation] Implement the text and TUI `[worktree]`
      markers and pass `epic["location"]` to `epic_markdown` at the
      epic-detail call site in `dashboard.py`; run the 3.3 tests green.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 4.2 [req: *] Run `plugins/s/skills/build/tests/` (no `textual`
      installed) and `plugins/s/skills/build/tests_textual/`; both suites
      green.
