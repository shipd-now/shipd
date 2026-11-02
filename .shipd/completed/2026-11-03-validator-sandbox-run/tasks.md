## 1. Sandbox config key

- [x] 1.1 [req: sandbox-config-key] In `plugins/s/skills/build/tests/test_config_registry.py`, add a `sandbox` entry to the `ROWS` table as `("repo", "an object with fake_bin (a relative path) and env (a map of variable names to relative paths)", None)`. Add `test_sandbox_validator` asserting that the well-formed value from the spec's first scenario yields no finding, and that `{"env": {"X": "../outside"}}`, `{"fakebin": "x"}`, `{"fake_bin": "/abs"}`, `{"env": {"bad-name": "x"}}` and `"str"` each raise or report an error naming `sandbox`, using the same call style `test_structural_validators` uses. Run the file and observe the failures.
- [x] 1.2 [req: sandbox-config-key] In `plugins/s/skills/build/scripts/spec_common.py`, add `"sandbox"` to `RECOGNIZED_CONFIG_KEYS` in alphabetical position, between `"room"` and `"statusline"`.
- [x] 1.3 [req: sandbox-config-key] In `plugins/s/skills/build/scripts/config_registry.py`, add `_validate_sandbox(value, path)` next to `_validate_retention`. It accepts a dict whose keys are a subset of `{"fake_bin", "env"}`. `fake_bin` is a non-empty string that is not absolute and has no `..` path segment. `env` is a dict whose keys match `^[A-Z_][A-Z0-9_]*$` and whose values meet the same rule as `fake_bin`. Any other value calls `_bad("sandbox", path, <expected text>, value)`. Add the `_row("sandbox", _validate_sandbox, <hint from 1.1>, "repo")` row to `REGISTRY` in alphabetical position. Run `test_config_registry.py` until it passes.
- [x] 1.4 [req: sandbox-config-key] In `plugins/s/skills/build/references/shipd.config.example.json`, add a `"// sandbox"` comment entry beside the other top-level `//` key entries. It reads: "The sandbox the `sandbox-run.sh` wrapper applies: `fake_bin`, a repo-relative directory prepended to `PATH`, and `env`, a map of variable names to paths under the sandbox's `state/` directory. An object; no default (undeclared means generic redirection only)." Run `test_config_sample.py` and confirm it passes.
- [x] 1.5 [req: sandbox-config-key] In `docs/customise.md`'s "The recognized keys" table, add the row `| \`sandbox\` | What \`sandbox-run.sh\` applies for the validator: \`fake_bin\` (a repo-relative directory prepended to \`PATH\`) and \`env\` (variable names mapped to paths under the sandbox root). Undeclared means generic redirection only. |` after the `voice` row.

## 2. The wrapper

- [x] 2.1 [req: sandbox-run-entry-point, sandbox-run-leak-refusal, sandbox-run-project-config] Add `plugins/s/skills/build/tests/test_sandbox_run.py`. It drives `sandbox-run.sh` by subprocess in the style of `test_claim_task.py`. Each test uses a temp repo (`git init`), a temp fake HOME passed as `HOME`, and `TMPDIR` set to a separate temp directory. Write one test per scenario in `.shipd/planned/validator-sandbox-run/specs/validator-sandbox/spec.md` under the requirements `sandbox-run-entry-point`, `sandbox-run-leak-refusal` and `sandbox-run-project-config`, asserting the exact exit codes and messages the plan's `## Implementation` gives. The uncreatable-root test sets `TMPDIR` to a path under a regular file. The repo-under-home test places the temp repo inside the fake HOME. The config tests write `.shipd-config.json` into the temp repo. Run the file and observe it fail.
- [x] 2.2 [req: sandbox-run-entry-point, sandbox-run-leak-refusal, sandbox-run-project-config] Add `plugins/s/skills/build/scripts/sandbox_run.py`, stdlib-only, with a module docstring. It implements the CLI, root, banner, env, config and leak-refusal rules exactly as the plan's `## Implementation` states. It reads the real HOME from `os.environ["HOME"]` and the temp base from `tempfile.gettempdir()` before building the child env. It resolves the repo root with `git rev-parse --show-toplevel`, falling back to `os.getcwd()`, and reads config with `spec_common.resolve_config(repo_root)`. It runs the command with `subprocess.run(["bash", "-c", cmd], env=child_env)` and exits with its return code.
- [x] 2.3 [req: sandbox-run-entry-point] Add `plugins/s/skills/build/scripts/sandbox-run.sh` (mode 0755): `#!/usr/bin/env bash`, a header comment naming the script's purpose and `sandbox_run.py`, then `exec python3 "$(cd "$(dirname "$0")" && pwd)/sandbox_run.py" "$@"`. Run `test_sandbox_run.py` until it passes.

## 3. Agent contracts and spawn messages

- [x] 3.1 [req: agent-sandbox-contract] In `plugins/s/skills/build/tests/test_subagent_contract.py`, add `SandboxContractTest`. It asserts that `validator.md` has a `## Sandbox` section containing `<SANDBOX_RUN>`, `one quoted string` and `contract violation`, and that `sub-agent.md` contains `<SANDBOX_RUN>`. It also asserts that each of `sub-agent.md` and `validator.md` under `plugins/s/agents/` (body after the closing `---` frontmatter line) equals its `plugins/s/harness/agents/` twin (body after the first `<!-- description: ... -->` line), with leading blank lines stripped on both sides. Run it and observe the failures.
- [x] 3.2 [req: agent-sandbox-contract] In `plugins/s/agents/validator.md`, change the spawn-message sentence to "supplies **the change name** and **the absolute path of `sandbox-run.sh`** (referred to below as `<SANDBOX_RUN>`) — and only those". Add a `## Sandbox` section before `## Guardrails` stating the contract in the plan's `## Implementation` "Contract" paragraph. It includes the form `bash <SANDBOX_RUN> '<command>'`, the phrase "one quoted string", the rule that `~` and `$HOME` go inside the single quotes, the read-only exemption, and the sentence "A raw `gh`, `git`, or script call outside the wrapper is a contract violation."
- [x] 3.3 [req: agent-sandbox-contract] In `plugins/s/agents/sub-agent.md`, add `<SANDBOX_RUN>` to the spawn-message inputs sentence ("the absolute path of `sandbox-run.sh`, referred to below as `<SANDBOX_RUN>`"). Add one `## Guardrails` bullet: when a task exercises `gh`, git remotes or watcher scripts against fakes, run those commands as `bash <SANDBOX_RUN> '<command>'`.
- [x] 3.4 [req: agent-sandbox-contract] Copy the bodies edited in 3.2 and 3.3 into `plugins/s/harness/agents/validator.md` and `plugins/s/harness/agents/sub-agent.md`, keeping each file's first `<!-- description: ... -->` line unchanged. Run `test_subagent_contract.py` until it passes.
- [x] 3.5 [req: agent-sandbox-contract] In `plugins/s/skills/build/SKILL.md`, change the sub-agent spawn sentence near line 342 to list "the change name, the absolute `<CLAIM_SCRIPT>` path, the absolute `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/sandbox-run.sh` path (as `<SANDBOX_RUN>`), and any Orchestrator addenda". Change the Phase 5 validator sentence near line 528 to "its spawn message supplies only the change name and the absolute `sandbox-run.sh` path (resolve `${CLAUDE_PLUGIN_ROOT}` first)".

## 4. Version bump

- [x] 4.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, bump `version` one patch step above the value on `origin/main` (currently `0.6.360`, so `0.6.361`).

## 5. Verification

- [x] 5.1 [req: *] Run the whole suite with `python3 -B -m unittest discover -s plugins/s/skills/build/tests 2>&1 | grep -E "^(OK|FAILED)"` and confirm `OK`. Run `python3 plugins/s/skills/build/scripts/spec_lint.py validator-sandbox-run` and confirm exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 38 | 26.3k |
| SubagentHandback | 3 | 4.0k |
| SendMessage | 1 | 1.2k |
| Agent | 2 | 979 |
| (no tool) | 0 | 617 |
| Monitor | 2 | 381 |
| ToolSearch | 1 | 239 |
| **Total** | 47 | 33.8k |
