# Tasks — worktree-telemetry

## 1. Worktree-aware transcript discovery

- [x] 1.1 [req: robust-source-discovery-and-degradation] Add failing tests in
      `plugins/s/skills/build/tests/test_build_report.py` (new test class,
      using tmp dirs and `CLAUDE_CONFIG_DIR`): `resolve_project_root` returns
      the main checkout for a fake linked worktree (a `.git` *file* containing
      `gitdir: <main>/.git/worktrees/<name>`), resolves a relative `gitdir:`
      against the worktree dir, returns the directory unchanged for a normal
      `.git` directory and for a submodule-style `gitdir: .../.git/modules/x`;
      and transcript discovery prefers the directory's own existing slug dir
      but falls back to the main checkout's slug dir when the own slug is
      absent. Run the file and observe the new tests fail.
- [x] 1.2 [req: robust-source-discovery-and-degradation] In
      `plugins/s/skills/build/scripts/build_report.py`, add
      `resolve_project_root(project_dir)` per the plan's Implementation
      decisions and wire the prefer-own-slug/fallback logic into transcript
      discovery (used by both the default and `--transcript` paths that call
      `transcript_dir`). Confirm the 1.1 tests pass.

## 2. Ship

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.1.6` → `0.1.7`.
- [x] 2.2 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py worktree-telemetry`;
      everything green.
