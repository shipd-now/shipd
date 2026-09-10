## 1. The writer

- [x] 1.1 [P1] [req: workspace-map-verbs] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for a new `save_repo_map(ws_root, repos)` in
      `plugins/s/skills/build/scripts/spec_common.py`: writing to an absent
      file creates it with only the `repos` key; writing over a file
      carrying a `workspace_root` key preserves that key byte-for-byte; a
      malformed existing file raises the load's `ConfigError` and writes
      nothing; output is pretty-printed JSON with a trailing newline that
      `load_repo_map` round-trips. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the worktree root and observe the failures.
- [x] 1.2 [P2] [req: workspace-map-verbs] Implement `save_repo_map` beside
      `load_repo_map` in `spec_common.py` until 1.1 passes.

## 2. The verbs

- [x] 2.1 [req: workspace-map-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing CLI
      tests for `workspace-map` against a fixture workspace declaring one
      member: bare form lists entries with stored value and resolved
      destination (and the unknown-key note); `set` with a declared member
      path writes the verbatim value and appends a
      `.shipd-workspace.local.json` line to the root `.gitignore` outside
      the marked member block (idempotent on a second `set`); `set` with an
      undeclared member path exits non-zero naming the declared paths and
      writes nothing; `set` to a non-existent target writes and warns on
      stderr; `remove` deletes exactly its entry and a second identical
      `remove` exits non-zero; every form outside a workspace fails with
      the standard no-workspace error.
- [x] 2.2 [req: workspace-map-verbs] Implement the `workspace-map` verb
      (bare/set/remove) in `plugins/s/skills/build/scripts/spec_status.py`
      beside the other workspace verbs, routed through `load_repo_map` /
      `save_repo_map` / `member_dest`, with the gitignore ensure-line
      helper in `spec_common.py`, until 2.1 passes.

## 3. The skill verb, docs, version

- [x] 3.1 [req: workspace-setup-skill] In
      `plugins/s/skills/workspace/SKILL.md`, add `map` to the verb
      dispatch and a "`map` — guided member mapping" section: run
      `workspace-sync --json` for the member list; for each unmapped
      member propose the plan's matching clone-source checkout when one
      exists, else invite a typed path; one question round; drive
      `workspace-map set` per accepted member; report already-mapped
      members without re-asking; finish on the bare `workspace-map`
      listing; never edit the map file by hand. Keep `sync` and `clone`
      question-free, and update the skill's Ending section accordingly.
- [x] 3.2 [P3] [req: workspace-map-verbs] Extend `docs/workspaces.md`'s
      member-map section with the three verb forms, the gitignore
      ensure-line, and the `/s:workspace map` flow.
- [x] 3.3 [P3] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from
      the version main carries at build time (`0.6.199` at planning) to
      the next patch.

## 4. Verification

- [x] 4.1 [req: *] From the worktree root, run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm `OK`. Then exercise the real verb against a throwaway
      workspace fixture: `set` a member to a throwaway checkout, confirm
      the bare listing and `workspace-show`'s mapped annotation agree,
      `remove` it, and confirm the listing empties while the
      `.gitignore` line remains.
