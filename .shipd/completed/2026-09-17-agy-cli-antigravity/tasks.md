## 1. AGY CLI registry adapter

- [x] 1.1 [req: registry-data, harness-read-verbs] In `plugins/s/skills/build/tests/test_harness_registry.py`, add focused tests that pin every `agy` registry field, distinguish it from `antigravity`, and assert `shipd harness show agy` reports both skill paths. Run that test file and observe the new tests fail because `agy` is absent.
- [x] 1.2 [req: registry-data, harness-read-verbs] In `plugins/s/skills/build/scripts/harness_registry.py`, add the `agy` entry after `antigravity` with name `Antigravity CLI`, repo pattern `.agents/skills/shipd-{command}.md`, user directory `~/.gemini/antigravity-cli/skills/`, YAML frontmatter `("name", "description")`, and features `("subagents", "file-references", "background-tasks")`; confirm the focused tests pass.
- [x] 1.3 [req: registry-data, harness-read-verbs] Run `plugins/s/skills/build/tests/test_harness_registry.py`, `test_harness_generate.py`, and `test_install_tui.py`; then use isolated temporary repo and HOME directories to verify `plugins/s/bin/shipd harness add agy --root <tmp>` and `plugins/s/bin/shipd harness add agy --user` generate owned skills at the specified paths.

## 2. Documentation and release metadata

- [x] 2.1 [P1] [req: harness-mode-docs] In `README.md`, update the interactive harness-picker count from fourteen to fifteen without changing the surrounding installation behavior.
- [x] 2.2 [P1] [req: *] In `plugins/s/.claude-plugin/plugin.json`, advance the plugin version from `0.6.223` to `0.6.224`.

## 3. Verification

- [x] 3.1 [req: registry-data, harness-read-verbs, harness-mode-docs] Run the complete engine unittest suite, run `plugins/s/bin/shipd harness` and `plugins/s/bin/shipd harness show agy`, and confirm the list has fifteen entries while the AGY entry reports its repo/user paths, frontmatter, and three features.
