# Tasks

## 1. Planner function (spec_common.py)

- [x] 1.1 [req: sync-materialization-planning, clone-sources-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for `plan_workspace_sync(ws_root, config)` over tempdir fixtures with
      real local git repos (origins set to fake path URLs via
      `git remote add origin`): present work-tree member → action `none`;
      present member with mismatched origin → `none` plus a drift note naming
      both URLs; present non-git directory → state `occupied` with a drift
      note; absent member with a matching work-tree candidate under a
      `clone_sources` dir → action `worktree` naming the source and an
      advisory command; absent member whose only candidate is bare → action
      `reference-clone`; absent member with a url and no candidate → action
      `clone`; path-only absent member → action `unmaterializable`;
      undeclared `clone_sources` → action `clone` (no probing); first-match
      wins across two declared source dirs; gitignore record lists a missing
      member path and a stale extra line.
- [x] 1.2 [req: sync-materialization-planning, clone-sources-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `plan_workspace_sync` plus local probe helpers (work-tree, bare, and
      origin-URL checks via subprocess git; `~` expansion of
      `clone_sources`), reusing `repo_entry_path` and the marked-block
      constants; confirm the 1.1 tests pass.

## 2. Verb (spec_status.py)

- [x] 2.1 [req: workspace-sync-verb, clone-sources-key] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests
      for `workspace-sync`: keyed member blocks and a `gitignore:` section
      with exit 0 on a plan containing drift and unmaterializable entries;
      `--json` lines each parsing as JSON objects with a `kind` field;
      `--write-gitignore` rewriting only the marked block (content outside
      the markers byte-identical) and the flagless run writing nothing; a
      malformed registry exiting non-zero with findings; a malformed
      `clone_sources` value exiting non-zero naming the key; a no-workspace
      run exiting non-zero.
- [x] 2.2 [req: workspace-sync-verb, clone-sources-key] In
      `plugins/s/skills/build/scripts/spec_status.py`, implement the
      `workspace-sync` verb (plan rendering, `--json`, guarded
      `--write-gitignore` via the engine's block writer, registry and
      `clone_sources` validation, no-workspace error); confirm the 2.1 tests
      pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      the version on remote main (0.6.14 at planning time — re-check before
      editing; other changes merge concurrently).
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run.
