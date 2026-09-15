# docs-lint-config-filename

- [x] 1.1 [P1] [req: document-lint-cli] Read `plugins/s/skills/document/scripts/docs_lint.py` and confirm where a whole-file check belongs: `check_file` calls `check_marker` then `check_text`, and `check_text` goes through `collect_units`, which strips fenced content. Confirm by reading `plugins/s/skills/build/scripts/spec_common.py` that `CONFIG_FILENAME` is `.shipd-config.json`, and report both findings before writing code.
- [x] 2.1 [P2] [req: document-lint-cli] Add a whole-file artifact-name check to `plugins/s/skills/document/scripts/docs_lint.py`, called from `check_file` beside `check_marker` so it sees every line including fenced blocks. Report an error for the spelling `shipd.config.json`, and for `shipd-config.json` only when no dot, word character, or hyphen precedes it — the correct `.shipd-config.json` must never match. The message SHALL name `.shipd-config.json` as the file the engine reads. Keep the module stdlib-only, and keep findings sorted by line as `check_file` already does.
- [x] 2.2 [P2] [req: document-lint-cli] Record the rule in `plugins/s/skills/document/references/standard.md`, under its `## Documentation rules` section, stating that a doc naming a configuration file other than `.shipd-config.json` is an error and that `shipd.config.example.json` is the annotated sample rather than a file the engine reads. Match the surrounding rules' wording and length.
- [x] 3.1 [P3] [req: document-lint-cli] Add tests to `plugins/s/skills/document/tests/test_docs_lint.py` covering all five new scenarios in the delta: `shipd.config.json` in prose errors; `.shipd-config.json` is clean; `shipd.config.example.json` is clean; a dot-less `shipd-config.json` errors; and `shipd.config.json` inside a fenced code block still errors. Follow the file's existing test style rather than introducing a new one.
- [x] 3.2 [P3] [req: *] Bump the version in `plugins/s/.claude-plugin/plugin.json` by one patch level, since this change touches `plugins/s/` and the cache snapshot is keyed by version.
- [x] 4.1 [req: *] Run `python3 -m pytest plugins/s/skills/document/tests/ -q` (or the repo's usual runner for that directory) and report the result. Then run the linter over the whole corpus exactly as CI does — `find docs -name '*.md' -not -path 'docs/retros/*'` piped into `docs_lint.py` — and confirm it still exits 0, since every page now names the configuration file correctly. Report any page the new check flags rather than editing the check to let it pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 77 | 16.4k |
| Edit | 7 | 5.7k |
| (no tool) | 0 | 3.6k |
| Agent | 3 | 1.5k |
| Read | 5 | 1.2k |
| **Total** | 92 | 28.4k |
