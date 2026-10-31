## 1. The init-status verb

- [x] 1.1 [req: layout-status-verb] Add `class TestInitStatusVerb` to
      `plugins/s/skills/build/tests/test_spec_status.py` (after
      `TestInitVerb`), running `python3 SCRIPT init-status --root <root>` with
      `HOME` set to a temp directory and `SHIPD_UNATTENDED` removed from the
      environment unless a test sets it. Cover every scenario of
      `layout-status-verb`: bare root, repo `{"dir": "specs"}` config, partial
      `.shipd/verified/` layout, parent `.shipd-config.json` declaring
      `workspace`, root after `init`, `SHIPD_UNATTENDED=1` and `--unattended`,
      `SHIPD_UNATTENDED=0`, `--json`, and malformed repo config. Assert the
      bare-root run leaves the directory empty. Run it and observe it fail.
- [x] 1.2 [req: layout-status-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `cmd_init_status(root, unattended=False, as_json=False)` after
      `cmd_init`, implementing the verdict, unattended, action, text, and
      JSON rules exactly as `plan.md`'s Implementation states.
- [x] 1.3 [req: layout-status-verb] In `spec_status.py` `main`, add the
      `init-status` subparser after `init` (repeat `--root` with
      `default=argparse.SUPPRESS`, add `--unattended` as `store_true`, call
      `_add_json_flag`), change the compat-gate guard to
      `args.verb not in ("init", "init-status")`, and dispatch to
      `cmd_init_status(root, args.unattended, args.json)`. Confirm
      `TestInitStatusVerb` and `TestInitVerb` pass.

## 2. The shipd init status mode

- [x] 2.1 [req: cli-init-status-mode] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add tests: `INIT_MODES`
      equals `{None: ("spec_status.py", ["init"]), "status":
      ("spec_status.py", ["init-status"])}`; `shipd init status --root <tmp>`
      prints `verdict: first-run`, exits 0, and creates nothing; `shipd init
      --root <tmp>` still prints `all shipd directories are ready`; the help
      banner contains `init [status] [--root DIR]`. Run and observe failure.
- [x] 2.2 [req: cli-init-status-mode] In `plugins/s/bin/shipd`, add
      `INIT_MODES` beside `WIKI_MODES` with a comment in the same style, and in
      `main` add an `if verb == "init":` mode block identical in shape to the
      `wiki` block.
- [x] 2.3 [req: cli-init-status-mode] In `plugins/s/bin/shipd` `USAGE`,
      replace the `init [--root DIR]` line with `init [status] [--root DIR]`
      plus an indented continuation saying `status` reports `first-run`,
      `layout-missing`, or `ready`. Confirm the 2.1 tests pass.
- [x] 2.4 [req: cli-init-status-mode] In `docs/cheatsheet.md`, change the
      `init [--root DIR]` row to `init [status] [--root DIR]` and add that
      `status` reports `first-run`, `layout-missing`, or `ready` and the action
      to take, writing nothing.

## 3. Unattended autopilot sessions

- [x] 3.1 [req: session-turn-result-text] In
      `plugins/s/skills/build/tests/test_session_driver.py` `ResultTextTest`,
      add a test with a fake binary printing
      `{"session_id":"s1","result":"$SHIPD_UNATTENDED"}` (shell-expanded),
      asserting `run_turn_result(..., env={"SHIPD_UNATTENDED": "1"})` returns
      text `1` and a run with no `env` and the variable unset returns `""`.
      Run and observe failure.
- [x] 3.2 [req: session-turn-result-text] In
      `plugins/s/skills/build/scripts/session_driver.py`, add `import os`, add
      `env=None` to `run_turn` (forwarded) and `run_turn_result`, and pass
      `env=None if env is None else {**os.environ, **env}` to
      `subprocess.run`. Update the `run_turn_result` docstring. Confirm 3.1
      passes.
- [x] 3.3 [req: unattended-session-env] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add `env=None` to the
      `fake_run_turn` signature in `ProductionSessionEffortTest`, then add a
      test class asserting the session seam's recorded `env` and the judge
      seam's recorded `env` (fake `session_driver.run_turn_result` returning
      `(True, None, "s1", "")`) both equal `{"SHIPD_UNATTENDED": "1"}`, and
      that `SHIPD_UNATTENDED` is absent from `os.environ` afterwards. Run and
      observe failure.
- [x] 3.4 [req: unattended-session-env] In
      `plugins/s/skills/build/scripts/autopilot.py`, define
      `UNATTENDED_ENV = {"SHIPD_UNATTENDED": "1"}` near `SHIPD_BIN`; pass
      `env=UNATTENDED_ENV` from the runner in `_make_session_fn` and from
      `judge_fn` in `_make_judge_fn`, and in `judge_fn` replace
      `effort=effort` with `effort=model`. Confirm 3.3 passes.

## 4. Verification

- [x] 4.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      by one patch level (from its current value on this branch, e.g.
      `0.6.354` → `0.6.355`), per AGENTS.md's plugin-version rule.
- [x] 4.2 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests` and grep the output for `OK` or
      `FAILED`; fix any failure. Run `python3
      plugins/s/skills/build/scripts/spec_lint.py init-status` clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 56 | 21.3k |
| SubagentHandback | 7 | 6.3k |
| Monitor | 13 | 2.8k |
| Agent | 3 | 959 |
| (no tool) | 0 | 906 |
| ToolSearch | 3 | 311 |
| Skill | 1 | 73 |
| TaskStop | 1 | 60 |
| **Total** | 84 | 32.7k |
