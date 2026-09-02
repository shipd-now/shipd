## 1. Store resolution

- [x] 1.1 [req: store-root-key, store-repo-folder-name] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for external store resolution: (a) a workspace-level
      `.shipd-config.json` declaring `store_root: "shipd-store"` makes a
      member repo with no config of its own resolve its content directory to
      `<ws>/shipd-store/<repo-basename>`; (b) a relative value resolves
      against the declaring config file's directory, not the start
      directory; (c) `~` expands; an absolute value is used as-is; (d) an
      empty or non-string value raises `ConfigError` naming `store_root`;
      (e) with no `store_root`, `specs_dir` returns `<root>/<dir>` unchanged;
      (f) with a real `git init` repo plus `git worktree add`, resolution
      from the linked worktree yields the same store folder as from the main
      checkout; (g) a non-git directory falls back to its own basename. Run
      the file and observe the new tests fail.
- [x] 1.2 [req: store-repo-folder-name] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `repo_store_folder(root)`: run
      `git rev-parse --path-format=absolute --git-common-dir` from `root`
      via `subprocess.run` (same guard style as `_inside_git_work_tree`);
      on success return the basename of the printed path's parent directory,
      on any failure return `os.path.basename(os.path.abspath(root))`.
      Memo-cache the result in a module-level dict keyed by
      `os.path.realpath(root)`.
- [x] 1.3 [req: store-root-key] In `spec_common.py`, add
      `store_root_dir(root)` returning the resolved external store root or
      `None`: read `store_root` from `resolve_config(root)`, validate
      non-empty string (`ConfigError` naming `store_root` otherwise),
      `os.path.expanduser`, and resolve a relative result against
      `os.path.dirname` of the declaring config path taken from the
      provenance map. Rework `specs_dir(root)` to return
      `os.path.join(store, repo_store_folder(root))` when `store_root_dir`
      yields a store, else `<root>/<dir>` as today. Run the 1.1 tests and
      observe them pass.

## 2. External store auto-commit

- [x] 2.1 [req: store-autocommit] In
      `plugins/s/skills/build/tests/test_spec_emit.py` and
      `plugins/s/skills/build/tests/test_spec_merge.py`, add failing tests:
      installing a change (and merging/archiving one) for a repo whose
      `store_root` resolves into a git-initialized store directory produces
      a local commit in the store scoped to the written files only; the same
      operations with no `store_root` create no commit in the repo; a
      non-git store directory succeeds with no commit attempted.
- [x] 2.2 [req: store-autocommit] In `spec_common.py`, add
      `store_autocommit(root, paths, subject)`: return `False` without
      touching git when `store_root_dir(root)` is `None`; otherwise delegate
      to the existing `wiki_autocommit(specs_dir(root), paths, subject)`,
      inheriting its no-op-outside-a-work-tree, scoped-commit, and
      warn-and-continue behavior.
- [x] 2.3 [req: store-autocommit] Wire `store_autocommit` into the artifact
      writers, each call passing the exact written paths: change install in
      `plugins/s/skills/build/scripts/spec_emit.py`, merge/archive in
      `spec_merge.py`, the plan rewrite in `spec_gate.py`, and `set-status`
      in `spec_status.py`. Run the 2.1 tests and observe them pass.

## 3. config-show reporting

- [x] 3.1 [req: config-show-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add a failing test:
      `config-show` for a root whose config declares `store_root` prints a
      line carrying the resolved absolute external content directory path.
- [x] 3.2 [req: config-show-verb] In `spec_status.py`'s `cmd_config_show`,
      when `store_root` is declared print the resolved external content
      directory (e.g. `store: <absolute path>` after the `content-dir:`
      line). Run the 3.1 test and observe it pass.

## 4. Docs and version

- [x] 4.1 [req: store-root-key] In `docs/portable-workspaces.md`, add a
      section documenting `store_root`: the workspace-wide declaration that
      makes every member repo store artifacts at
      `<ws>/<store>/<repo-name>/` with zero per-repo config, the
      dedicated-artifacts-repo pattern, relative-to-declaring-file
      resolution, the auto-commit behavior, and the documented limitations
      (worktree-guard/statusline blindness, basename collisions, no CI
      artifacts in bare checkouts).
- [x] 4.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` and run the full engine test
      suite `plugins/s/skills/build/tests/` (without `textual` installed),
      confirming it passes as the change's verification barrier.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 114 | 25.5k |
| Edit | 20 | 7.8k |
| Read | 23 | 2.8k |
| Agent | 2 | 939 |
| (no tool) | 0 | 200 |
| ToolSearch | 1 | 24 |
| Monitor | 1 | 2 |
| **Total** | 161 | 37.3k |
