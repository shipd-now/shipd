## 1. Correct AGY registry paths

- [x] 1.1 [req: registry-data] In `plugins/s/skills/build/tests/test_harness_registry.py`, update the AGY assertions for `.agents/skills/shipd-{command}/SKILL.md`, `~/.gemini/config/skills/shipd-{command}/`, and its legacy user pattern; run the file and observe failure against `0.6.224`.
- [x] 1.2 [req: registry-data] In `plugins/s/skills/build/scripts/harness_registry.py`, correct AGY's repo and user paths and add its marker-safe legacy user pattern; confirm the registry tests pass.

## 2. Generate nested Agent Skills

- [x] 2.1 [req: harness-add-remove] In `plugins/s/skills/build/tests/test_harness_generate.py`, add failing path and CLI-generation tests for AGY's nested repo and user `SKILL.md` files, plus a regression assertion for an existing harness's user path.
- [x] 2.2 [req: harness-add-remove] In `plugins/s/skills/build/scripts/harness_generate.py`, format `{command}` in `user_dir` before joining the repo-pattern-derived basename; confirm nested AGY and unchanged existing-harness path tests pass.

## 3. Migrate broken 0.6.224 output

- [x] 3.1 [req: harness-add-remove] In `plugins/s/skills/build/tests/test_harness_generate.py`, add failing tests that AGY user add and remove delete marker-owned legacy flat files but preserve unmarked legacy files.
- [x] 3.2 [req: harness-add-remove] In `plugins/s/skills/build/scripts/harness_generate.py`, resolve legacy patterns generically and clean only marker-owned legacy files during user add and remove; confirm all migration and ownership tests pass.

## 4. Release and verification

- [x] 4.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, advance the version from `0.6.224` to `0.6.225`.
- [x] 4.2 [req: registry-data, harness-add-remove] Run the full engine unittest suite and spec lint; then generate AGY into isolated repo and HOME directories, confirm every command uses `<skill>/SKILL.md`, and confirm an owned legacy flat file is removed.
