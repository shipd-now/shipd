## 1. Registry entry

- [x] 1.1 [req: registry-data] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add a
      `test_opencode_paths` method to `ResearchedPathsTest` asserting
      `hr.get("opencode")` has `repo_pattern`
      `.opencode/commands/shipd-{command}.md`, `user_dir`
      `~/.config/opencode/commands/`, `dialect` `yaml`, `frontmatter`
      `("description",)`, and `features` `("subagents", "file-references")`.
      Run the file with `python3 -m unittest` and observe the new test fail
      — the entry does not exist yet.
- [x] 1.2 [req: registry-data] In
      `plugins/s/skills/build/scripts/harness_registry.py`, append the
      `opencode` entry after `oh-my-pi` in `HARNESSES`: id `opencode`, name
      `OpenCode`, `repo_pattern` `.opencode/commands/shipd-{command}.md`,
      `user_dir` `~/.config/opencode/commands/`, dialect `yaml`,
      frontmatter `("description",)`, features
      `("subagents", "file-references")`. Confirm
      `test_harness_registry.py` now passes.
- [x] 1.3 [req: harness-read-verbs] Run `python3 -m unittest` over
      `plugins/s/skills/build/tests/test_harness_registry.py`,
      `test_harness_verb.py`, and `test_harness_generate.py` — the
      registry-iterating suites must pass with thirteen entries — and run
      `plugins/s/bin/shipd harness`, confirming an `opencode` line appears
      with exit code 0.

## 2. Documentation and version

- [x] 2.1 [req: harness-mode-docs] In `README.md` (the "registry's twelve
      harnesses" sentence, currently line 87), change "twelve" to
      "thirteen".
- [x] 2.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.150` to `0.6.151`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 51 | 12.9k |
| (no tool) | 0 | 3.6k |
| Edit | 4 | 1.1k |
| Read | 10 | 1.1k |
| Agent | 2 | 737 |
| ToolSearch | 1 | 601 |
| WebFetch | 1 | 184 |
| **Total** | 69 | 20.1k |
