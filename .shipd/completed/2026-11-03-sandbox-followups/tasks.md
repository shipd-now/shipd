## 1. Path-proof autopilot test

- [x] 1.1 [req: *] In `plugins/s/skills/build/tests/test_autopilot.py`, change `test_bare_entries_keep_todays_prompts` exactly as the plan's `## Implementation` "Autopilot test" paragraph states. Run the file and confirm it passes.

## 2. Leak check and toolchain locators

- [x] 2.1 [req: sandbox-run-leak-refusal] In `plugins/s/skills/build/tests/test_sandbox_run.py`, add three tests to `LeakRefusalTest`, one per new scenario in `specs/validator-sandbox/spec.md`. The symlink test creates a real directory, a symlink to it, passes `HOME=<symlink>`, places the git repo inside it, and names a file through `<symlink>/<repo>/`. The pyenv tests write an executable shim at `<home>/.pyenv/shims/python3` that execs `${PYENV_ROOT:-$HOME/.pyenv}/versions/x/bin/python3`, symlink that target to `sys.executable`, and prefix `PATH` with the shim directory. Run the file and observe the three failures.
- [x] 2.2 [req: sandbox-run-leak-refusal] In `plugins/s/skills/build/scripts/sandbox_run.py`, implement the "Repo forms" and "Toolchain locators" paragraphs of the plan's `## Implementation`. Update the module docstring to name both rules. Run `test_sandbox_run.py` until it passes.

## 3. Ship

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.361` to `0.6.362`.
- [x] 3.2 [req: *] Run `python3 -B -m unittest discover -s plugins/s/skills/build/tests 2>&1 | grep -E "^(OK|FAILED)"` and confirm `OK`. Run the linter on `sandbox-followups` and confirm exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 39 | 22.1k |
| SubagentHandback | 2 | 1.9k |
| (no tool) | 0 | 953 |
| Agent | 2 | 895 |
| Monitor | 1 | 131 |
| **Total** | 44 | 26.0k |
