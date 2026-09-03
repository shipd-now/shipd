# Tasks — workspace-universe-seam

## 1. The shared seam (spec_common)

- [x] 1.1 [req: workspace-universe-discovery] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add a test class
      for the universe seam: (1) a workspace root declaring two present repo
      dirs → `sc.workspace_project_roots(root)` yields both in project slug
      order and `sc.aggregation_universes(root)` lists `(None, root)` first;
      (2) resolved from inside a declared project repo → both return the
      single-universe forms; (3) an absent repo path, a duplicate real path
      (including via symlink), a `{"path": "."}` entry, a non-dict project
      entry, and an unparseable registry each skip silently; (4) no
      workspace discoverable → `[(None, root)]`. Run them and observe
      failure — the seam does not exist yet.
- [x] 1.2 [req: workspace-universe-discovery] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `workspace_project_roots(root)` and `aggregation_universes(root)` next
      to `registry_root`/`project_of`, implemented per plan.md's seam
      decision on `load_workspace` + `repo_entry_path` (trigger:
      `registry_root(root)` resolves AND `project_of(reg_root, root) is
      None`; slug-ordered projects, declaration-ordered repos, paths joined
      to the registry root; skip non-dirs, real-path duplicates, the
      invocation root's real path; `ConfigError` → `[]`). Confirm the 1.1
      tests pass.

## 2. Failing consumer tests first

- [x] 2.1 [P2] [req: epic-status-verbs, locate-verb, json-output, workspace-board-report] In
      `plugins/s/skills/build/tests/test_spec_status.py`: with a workspace
      fixture (root + declared project repo hosting an epic and a planned
      change) add tests for — `epic-show <slug>` from the workspace root
      printing a `project: <slug>` line after the metadata lines with member
      states derived from the project repo; the invocation root's universe
      winning a slug hosted in both (no `project:` line); `epic-sync` and
      `epic-set-status` still exiting non-zero on a project-hosted epic;
      `epic-show --json` carrying `project` (slug, and null for a
      root-hosted epic); `locate <change>` finding a project repo's planned
      change with a `project: <slug>` line, the root's block first when both
      host it, and `--json` rows always carrying `project` (slug or null);
      and the bare `show` board rendering identically to today on the same
      fixture (now via the shared seam). Run them and observe failure.
- [x] 2.2 [P2] [req: board-aggregation] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add
      `build_board` universe tests on the same fixture shape: a project
      universe epic aggregated with `project` set, `universe_root` the
      project repo (absolute), member states/locations derived from that
      repo, per-universe standalone rows carrying `project`; `--epic`
      resolving a project-hosted slug (and the root universe winning a
      duplicate); the board built from inside the member repo staying
      per-repo (`project` null everywhere); the human board and TUI epic
      group header rendering ` [<project>]` after any `[worktree]` marker;
      and `build_plan_launch` fed the epic's `universe_root` producing a
      worktree path and cwd under the project repo. Run them and observe
      failure.
- [x] 2.3 [P2] [req: metrics-engine] In
      `plugins/s/skills/build/tests/test_metrics.py`, add tests: an epic
      hosted only under `.worktrees/<name>` contributes its in-flight
      members to the WIP snapshot; a workspace root whose declared project
      repo hosts an epic contributes nothing from that project to `derive`'s
      result. Run them and observe failure (the worktree case fails today;
      keep the project case as a pin even if it passes).

## 3. spec_status.py implementation (sequential)

- [x] 3.1 [req: workspace-board-report] In
      `plugins/s/skills/build/scripts/spec_status.py`, delete
      `_workspace_project_roots` and build `_workspace_report_data`'s
      universe list from `sc.aggregation_universes(root)`; update the
      docstrings that named the deleted helper. Rendering and JSON stay
      byte-identical (the existing workspace-report tests must stay green).
- [x] 3.2 [req: epic-status-verbs, json-output] In `spec_status.py`, add
      `_epic_hosting_universe(root, slug)` → `(project, universe_root,
      hosting_root)` or `None`, probing each `sc.aggregation_universes`
      universe in order with the existing
      `_epic_hosting_root(universe_root, slug)`; route `cmd_epic_show` and
      `show`'s epic fallback through it — report data built by
      `_epic_report_data(universe_root, slug)`, data gaining `"project"`
      (slug or `None`), text printing `project: <slug>` directly after the
      metadata lines (after any `worktree:` line) only when project-hosted.
      Mutating epic verbs keep their current invocation-root resolution
      untouched.
- [x] 3.3 [req: locate-verb, json-output] In `spec_status.py`, extend
      `cmd_locate` to iterate `sc.aggregation_universes(root)` in order,
      running its existing planned/worktrees probe per universe; text blocks
      from a project universe append a `project: <slug>` line, JSON rows
      always carry `project` (slug or null), and the not-found error still
      names the probed locations.
- [x] 3.4 [req: epic-status-verbs, locate-verb, json-output, workspace-board-report] Run the 2.1 tests plus the existing
      workspace-report tests in `test_spec_status.py`; confirm all pass.

## 4. dashboard.py implementation (sequential)

- [x] 4.1 [req: board-aggregation] In
      `plugins/s/skills/build/scripts/dashboard.py`, rework `build_board` to
      iterate `sc.aggregation_universes(root)`: per universe run the
      existing pipeline (`_epic_slugs(universe_root)`,
      `_epic_board(universe_root, slug, hosting_root)`,
      `standalone_changes(universe_root, that_universe_member_slugs)`); tag
      every epic dict with `"project"` and absolute `"universe_root"` and
      every standalone row with `"project"`; resolve an explicit `epic`
      argument against the universes in order (first hosting universe wins,
      `ValueError` when none hosts it).
- [x] 4.2 [req: board-aggregation] In `dashboard.py`, render ` [<project>]`
      after the `[worktree]` marker in the human board's epic header and the
      TUI epic group header, and thread `epic["universe_root"]` (falling
      back to the board root) through every call site of
      `build_plan_launch`, `build_run_launch`, `build_epic_run_launch`, and
      `build_open_launch` — grep the TUI action dispatch for the four
      builders and replace the board-root argument at each.
- [x] 4.3 [req: board-aggregation] With `textual` installed
      (`pip install -r requirements.txt`), run the 2.2 tests and the rest of
      `plugins/s/skills/build/tests_textual/test_dashboard.py`; confirm all pass.

## 5. metrics.py implementation (sequential)

- [x] 5.1 [req: metrics-engine] In
      `plugins/s/skills/build/scripts/metrics.py`, replace the three direct
      `epics_dir` listings (the walks at metrics.py:423, metrics.py:526, and
      the epics block at metrics.py:1519) with
      `ss.all_epic_slugs_with_roots(root)`, reading each epic file from its
      hosting root, and resolve the single-epic paths (metrics.py:1291,
      metrics.py:1482) through `ss._epic_hosting_root(root, epic)` with the
      current root-relative path as the not-found fallback. Do NOT use
      `aggregation_universes` — metrics stays per-repo.
- [x] 5.2 [req: metrics-engine] Run the 2.3 tests plus the full
      `test_metrics.py`; confirm all pass.

## 6. Docs and version

- [x] 6.1 [P6] [req: epic-status-verbs, locate-verb, board-aggregation] In
      `plugins/s/skills/status/SKILL.md`, document that `epic-show` (and
      `show <epic>`) and `locate` resolve across declared workspace
      projects on workspace-level invocations — project-hosted results
      carrying a `project:` line — and that the workspace-report section's
      board behavior now extends to the dashboard board's project markers.
- [x] 6.2 [P6] [req: *] Bump `plugins/s/.claude-plugin/plugin.json`
      `version` from `0.6.170` to `0.6.171`.

## 7. Verification barrier

- [x] 7.1 [req: *] From the repo root run the full stdlib suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p
      "test_*.py"`, without `textual` importable; confirm green.
- [x] 7.2 [req: *] With `textual` installed, run the full
      `plugins/s/skills/build/tests_textual/` suite; confirm green. Fix any regression before
      checking this off.

## 8. Validator fixes (duplicate-slug universe identity in the TUI)

- [x] 8.1 [req: board-aggregation] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      regression tests for duplicate-slug universes: a board whose epic slug
      exists in the invocation root AND a declared project (and in two
      projects) must render each TUI group header with its OWN universe's
      marker (root copy unmarked, `[<project>]` on the project copy, never a
      sibling's), and `resolve_action_launch` / `BoardApp._epic_root` /
      `dispatch_epic_run` for the project copy's member must produce a cwd,
      worktree path, and autopilot `--root` under that project's repo — never
      another universe's. Run them and observe failure.
- [x] 8.2 [req: board-aggregation] In
      `plugins/s/skills/build/scripts/dashboard.py`, make every TUI epic
      lookup identity-based instead of slug-based: `_find_epic`
      (dashboard.py:1555) gains a project discriminator (resolve by
      `(slug, project)`, with the epic dict itself or its board index as the
      carried identity where the TUI currently stores a bare slug — group
      headers at ~4161, `resolve_action_launch` at ~1657 resolving the epic
      that actually hosts the named member, `BoardApp._epic_root` at ~4354,
      and `dispatch_epic_run`). Slug-alone resolution must remain correct
      when unambiguous (single-universe boards unchanged). Confirm the 8.1
      tests and the full textual + stdlib suites pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 465 | 112.7k |
| Read | 1590 | 82.3k |
| Edit | 62 | 30.3k |
| (no tool) | 0 | 11.7k |
| Write | 2 | 3.6k |
| SendMessage | 7 | 3.1k |
| Agent | 4 | 1.6k |
| ToolSearch | 7 | 1.4k |
| TaskStop | 2 | 58 |
| **Total** | 2139 | 246.8k |
