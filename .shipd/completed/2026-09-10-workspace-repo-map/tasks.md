## 1. The map and its seam

- [x] 1.1 [P1] [req: workspace-member-map] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for two new `spec_common` helpers: `load_repo_map(ws_root)` — absent
      `.shipd-workspace.local.json` yields `{}`; a valid `repos` object
      loads with values preserved verbatim; invalid JSON, a non-object top
      level, `{"repos": []}`, and an empty-string value each raise
      `ConfigError` naming the file — and `member_dest(ws_root, path)` —
      an unmapped path joins the workspace root with the manifest path; a mapped path returns the map
      value resolved absolute (a `~` value expanded, a relative value
      resolved against `ws_root`). Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the worktree root and observe the new cases fail.
- [x] 1.2 [P2] [req: workspace-member-map] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `REPO_MAP_FILENAME = ".shipd-workspace.local.json"`,
      `load_repo_map(ws_root)`, and `member_dest(ws_root, path)` beside the
      registry helpers (near `repo_entry_path`), with the tolerant/erroring
      behavior 1.1 encodes, until 1.1's cases pass.

## 2. Consumers

- [x] 2.1 [req: project-resolution] In `test_spec_common.py`, add failing
      tests: `project_of` resolves a file inside a mapped external checkout
      to the declaring project (map entry for the member's manifest path
      pointing outside `ws_root`), and existing containment behavior is
      unchanged for unmapped entries. Then extend
      `spec_common.project_of` to additionally match against
      `os.path.realpath(member_dest(...))` for mapped entries, same
      most-specific-wins scoring, until the tests pass.
- [x] 2.2 [req: sync-materialization-planning] In `test_spec_common.py`
      (planner tests), add failing cases: a mapped member pointing at an
      existing git checkout plans action `none` carrying the resolved
      mapped destination and no `command`; a mapped member whose
      destination does not exist plans state `absent`, action `none`, no
      command, and a drift note naming the mapped path; a mapped present
      checkout with mismatched origin keeps the origin-drift note. Then
      route `_plan_member`'s `dest` through `member_dest`, add the
      `mapped` field, and bypass the materialization ladder for mapped
      members, until the tests pass.
- [x] 2.3 [req: workspace-member-map] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing
      cases for `workspace-show`: a mapped member reports present via its
      mapped destination with a `[mapped -> <path>]` annotation (and a
      `mapped` field in the JSON report where the verb has one), and a map
      key matching no manifest path prints a note while the verb exits
      zero. Then implement in `spec_status.py`'s show path (the
      `os.path.join(ws_root, path)` presence probe, ~line 3273) routed
      through `member_dest`, until the tests pass.
- [x] 2.4 [req: workspace-member-map] Extend
      `spec_common.workspace_project_roots` to resolve each repo root
      through `member_dest` (keeping the existing realpath de-dup), with a
      `test_spec_common.py` case first: a mapped member's external
      checkout appears as that project's universe root. Observe it fail,
      then implement until green.

## 3. Docs and version

- [x] 3.1 [req: workspace-member-map] Add a "Mapping members to existing
      checkouts" section to `docs/workspaces.md`: the
      `.shipd-workspace.local.json` file and its `repos` shape, `~` and
      relative value resolution, the machine-local/never-committed nature,
      the planner's mapped behavior (always `none`, never materializes
      into a mapped path, drift note on a missing target), and the
      unknown-key note.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.198` -> `0.6.199`.

## 4. Verification

- [x] 4.1 [req: *] From the worktree root, run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm `OK` (baseline: green on main via the same invocation). Then
      exercise the real behavior: create a throwaway workspace fixture
      with one registry member, write a map pointing it at a throwaway git
      checkout elsewhere, and confirm `workspace-show` reports the mapped
      annotation and `workspace-sync --json` emits the mapped `none`
      record with no command.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 183 | 36.4k |
| Edit | 30 | 9.7k |
| Read | 15 | 994 |
| Agent | 2 | 973 |
| ToolSearch | 3 | 777 |
| (no tool) | 0 | 593 |
| Monitor | 3 | 41 |
| TaskStop | 1 | 17 |
| **Total** | 237 | 49.5k |
