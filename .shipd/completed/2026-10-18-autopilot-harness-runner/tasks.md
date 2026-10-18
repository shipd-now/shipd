## 1. The runner registry

- [x] 1.1 [req: harness-runners, shared-session-driver, session-turn-result-text]
      In `plugins/s/skills/build/tests/test_session_driver.py`, add tests: the
      `claude` runner's `argv` for a model and resume id is the pinned list; the
      `opencode` runner's `argv` is the pinned list with the prompt last; the
      `opencode` runner's parser reads the last `sessionID` and concatenates
      the `type == "text"` parts of a two-line JSONL fixture; the `opencode`
      runner rewrites `/s:plan` to `/shipd-plan` while the `claude` runner
      rewrites nothing; `runner_for("no-such-harness")` raises a named error;
      and a `run_turn_result(..., harness="opencode", binary=<fake>)` turn
      against a fake binary that prints an OpenCode JSONL transcript returns
      that session id and result text. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_session_driver.py'`
      and observe the new tests fail.
- [x] 1.2 [req: harness-runners, shared-session-driver, session-turn-result-text]
      In `plugins/s/skills/build/scripts/session_driver.py`, add a `RUNNERS`
      registry and `runner_for(harness_id)` (raising a named error for an
      unknown id), each runner carrying its default `binary`, an `argv`
      builder, a `parse` function, and a `rewrite` function. Change
      `run_turn_result` to take `harness="claude"` and `binary=None` (defaulting
      to the runner's binary), resolve the runner, rewrite the prompt through
      it, build the argv through it, and parse the transcript through it.
      `run_turn` and `drive` keep their contracts, threading `harness` through.

## 2. The autopilot selects a harness

- [x] 2.1 [req: harness-runners] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add tests that
      `--harness opencode` reaches the session function's `harness` argument,
      that the default is `claude`, and that the run report names the harness.
      Run the suite and observe the new tests fail.
- [x] 2.2 [req: harness-runners] In
      `plugins/s/skills/build/scripts/autopilot.py`, add a `--harness` option
      (default `claude`) and thread it through `_make_session_fn`,
      `_make_judge_fn`, `drive_member`, and the single-member drive to
      `session_driver.run_turn_result`. Move `_session_extra_args`'s plugin-dir
      and permission flags into the `claude` runner, passing the plugin
      directory and the resolved model to the runner instead. Rename the
      `claude_bin` parameter to `binary` and keep `--claude-bin` as the binary
      override. Add the harness to the run report.

## 3. Version bump

- [x] 3.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.324` to `0.6.325`.

## 4. Verify

- [x] 4.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_session_driver.py'`,
      `-p 'test_autopilot.py'`, then the whole
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `python3 -m unittest discover -s evals/tests`; all exit 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py autopilot-harness-runner`
      and confirm `OK`. Then a live smoke: `python3 plugins/s/skills/build/scripts/autopilot.py harness-agents --harness opencode --dry-run`
      prints the harness and drives nothing, and a single throwaway
      `session_driver` turn against a real `opencode run` in a temp directory
      returns a session id.
