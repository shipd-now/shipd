# Tasks — workspace-board-aggregation

## 1. Failing tests first

- [x] 1.1 [req: workspace-board-report, json-output] In
      `plugins/s/skills/build/tests/test_spec_status.py`, near the existing
      workspace-report tests (see `test_empty_workspace_reports_zeroes` and
      `test_bare_show_json_is_the_workspace_report`), add a test class for
      workspace-level board aggregation. Fixture: a temp workspace root whose
      `.shipd-config.json` declares `{"workspace": {"projects": {"proj-a":
      {"repos": [{"path": "proj-a"}]}, "proj-b": {"repos": [{"path":
      "proj-b"}]}}}}`, with `proj-a/` a repo holding an epic (stub table with
      members, one archived under `completed/`) and a standalone planned
      change, `proj-b/` absent on disk. Cover: (1) bare `show` from the
      workspace root counts proj-a's epic/members in the totals and renders
      its rows with a ` [proj-a]` marker; (2) member states derive from
      proj-a (the archived member lands in SHIPPED, rolled up as
      `<epic> [proj-a] (n)`); (3) proj-a's standalone change renders with
      epic column `standalone` and the marker; (4) the absent `proj-b` repo
      is skipped without error; (5) bare `show` run from inside `proj-a`
      reports only proj-a's universe with no markers (per-repo behavior
      unchanged); (6) `show --json` from the workspace root: proj-a rows
      carry `"project": "proj-a"`, invocation-root rows carry
      `"project": None`; (7) a root with no discoverable registry renders
      byte-identical to today (existing rows gain only `project: None` in
      JSON); (8) the same epic slug hosted in two declared project repos
      appears twice, distinguished by markers. Run the new tests and observe
      them fail — the aggregation does not exist yet.

## 2. Implementation (spec_status.py, sequential)

- [x] 2.1 [req: workspace-board-report] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `_workspace_project_roots(root)` next to `_workspace_epic_slugs`
      (~line 1394): resolve `reg_root = sc.registry_root(root)`; return `[]`
      when it is `None` or `sc.project_of(reg_root, root)` is not `None`;
      otherwise return `[(slug, abs_repo_root)]` for projects in slug order
      via `_load_projects(reg_root)`, each project's repos in declaration
      order via `sc.repo_entry_path`, path resolved
      `os.path.join(reg_root, rel)`; skip non-directories, real-path
      duplicates, and entries whose real path equals the invocation root's.
      Docstring states the trigger rule and the fail-soft skips.
- [x] 2.2 [req: workspace-board-report, json-output] Rework
      `_workspace_report_data` (~line 1404) to iterate universes
      `[(None, root)] + _workspace_project_roots(root)`: per universe,
      epics via `all_epic_slugs_with_roots(universe_root)`, member state via
      `_member_state_with_root(universe_root, mslug)` (worktree flag =
      hosting_root != universe_root), standalone via
      `standalone_changes(universe_root, that_universe_member_slugs)`
      (worktree flag = location != abspath(universe_root)); every row gains
      `"project"` (the universe's project slug or `None`); collect all epic
      rows first (root universe, then projects in slug order), then all
      standalone rows in the same universe order; totals sum across
      universes, `initiatives` counts distinct slugs across universes; epic
      slugs are never deduped across universes. Update the docstring.
- [x] 2.3 [req: workspace-board-report] Update `_workspace_report_lines`
      (~line 1484): non-shipped rows append a ` [<project>]` marker after
      the ` [worktree]` marker position when `row["project"]` is set; the
      SHIPPED rollup keys its counts dict by `(epic, project)` in insertion
      order and renders `<epic> [<project>] (<n>)` for project rows,
      `<epic> (<n>)` otherwise. Update the docstring.
- [x] 2.4 [req: workspace-board-report] Update the module docstring and
      help text in `spec_status.py` where they describe the bare-`show`
      report (~lines 24, 126, and the `show` help string ~line 3009) to say
      the board aggregates declared workspace projects on workspace-level
      invocations and stays per-repo inside a declared project repo.
- [x] 2.5 [req: workspace-board-report, json-output] Run the task-1.1 tests
      and confirm they now pass.

## 3. Docs and version

- [x] 3.1 [P1] [req: workspace-board-report] In
      `plugins/s/skills/status/SKILL.md`, update the "When there is no
      argument and no selection — the workspace report" section: state that
      from a workspace-level invocation (a root inside no declared project
      repo) the board also aggregates every declared `workspace.projects`
      repo present on disk, rows from a project carrying a `[<project>]`
      marker (and `<epic> [<project>] (<n>)` shipped rollups), while inside
      a declared project repo the board stays scoped to that repo.
- [x] 3.2 [P1] [req: *] Bump `plugins/s/.claude-plugin/plugin.json`
      `version` from `0.6.169` to `0.6.170`.

## 4. Verification barrier

- [x] 4.1 [req: *] Run the full stdlib-only engine suite from the repo
      root: `python3 -m pytest plugins/s/skills/build/tests/ -q` (no
      `textual` needed). Confirm it is green; fix any regression the
      aggregation introduced before checking this task off.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 79 | 21.8k |
| Write | 8 | 13.7k |
| Read | 22 | 3.1k |
| Edit | 19 | 2.6k |
| AskUserQuestion | 1 | 925 |
| Agent | 2 | 894 |
| (no tool) | 0 | 265 |
| **Total** | 131 | 43.3k |
