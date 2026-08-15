## 1. Doctor checks

- [x] 1.1 [req: doctor-verb] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: each check function
      branch via injected inputs (env dict, stub `which`, fake cache root,
      manifest version, stub gh runner) — python floor, git missing, config
      unreadable vs missing-content-dir-ok, gh absent/unauthenticated warns,
      textual missing warns, stale-snapshot warn, checkout dev-mode ok — plus
      the composed output shape (`ok|warn|fail` lines, closing `doctor:`
      line) and the exit contract (fail → 1, warn-only → 0).
- [x] 1.2 [req: doctor-verb] Implement the injectable check functions and
      `cmd_doctor` in `plugins/s/bin/shipd`, mirroring `cmd_list`'s
      in-binary pattern; subprocess use confined to the injectable gh
      runner. Run the 1.1 tests green.

## 2. Dispatch wiring

- [x] 2.1 [req: cli-dispatch] Add failing tests: `doctor` dispatches to
      `cmd_doctor` without exec-delegation, and the usage banner lists
      `doctor`.
- [x] 2.2 [req: cli-dispatch] Wire `doctor` into `main` beside `list` and add
      it to the `USAGE` banner in `plugins/s/bin/shipd`; unknown-verb and
      help behavior unchanged. Run the 2.1 tests green.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Run `plugins/s/skills/build/tests/` (no `textual`) and
      `plugins/s/skills/build/tests_textual/`; both green.
