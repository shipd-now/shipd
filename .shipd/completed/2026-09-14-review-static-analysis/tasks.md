# review-static-analysis

- [x] 1.1 [P1] [req: review-lint-subcommand] Add `plugins/s/skills/review/tests/test_semdiff_lint.py`, a stdlib-only `unittest` module building scratch git repositories (follow the fixture style already in `test_semdiff_files_context.py`) and asserting the whole contract, then confirm it FAILS before any other task is claimed. Cover: a marker file plus a resolvable binary yields state `ran` with an `argv` naming only the changed paths that linter owns; a marker with no resolvable binary yields `unavailable`; a detected linter owning no changed path yields `skipped` with no execution; a `package.json` lint script yields `not-run` without the opt-in and runs with it; a timeout or unparseable output yields `failed` with a stderr excerpt and exit `0`; the project-local npm binary directory wins over `PATH`; and `lint.disable` suppresses a fully detected linter. Stub the linter binaries with small executable scripts written into the scratch repo rather than requiring real linters to be installed — none of the four is present on this machine.
- [x] 2.1 [P2] [req: review-lint-subcommand] In `plugins/s/skills/review/scripts/semdiff.py`, add the detection layer: a module-level table mapping each of `ruff`, `flake8`, `pylint` and `eslint` to its marker files, its owned file extensions, and its machine-format argv template, plus a resolver that checks the project-local npm binary directory (the `.bin` folder inside a repository's `node_modules`) before `shutil.which`. Read the resolved `lint` configuration through the existing `spec_common.resolve_config` path that `_content_dir` already uses. Add no third-party import — the constitution binds this file to the standard library.
- [x] 2.2 [P2] [req: config-sample-coverage] Add `lint` to `RECOGNIZED_CONFIG_KEYS` in `plugins/s/skills/build/scripts/spec_common.py` (keep the tuple alphabetical) and document it in `plugins/s/skills/build/references/shipd.config.example.json` with a comment stating what it does and its default, per the registry's both-directions rule. Its members are `run_scripts` (boolean, default false) and `disable` (list of linter names).
- [x] 3.1 [P3] [req: review-lint-subcommand] In `semdiff.py`, add the `lint` subcommand itself: register it with `sub.add_parser` alongside the existing five, resolve endpoints through the same `resolve_endpoints` helper `diff` and `files` use, partition the changed paths by owned extension, run each detected linter under a per-linter timeout via `subprocess`, parse its machine output, and emit the single JSON object the delta specifies (`base`/`head`/`mode`, `linters`, `summary`). Never pass a fix or write flag. A non-zero linter exit is normal and is distinguished from a crash by whether the output parses; a crash, timeout, or unparseable output sets `failed` and the subcommand still exits `0`.
- [x] 4.1 [P4] [req: review-lint-step] Create `plugins/s/skills/review/references/linters.md`. Open with the level-1 title `# Linter output` and, directly beneath it, a condition sentence containing "reads this file" that shares at least 3 content words of 4+ letters with the `Load when` cell task 4.2 writes — measure this against the running agreement test rather than assuming, since two existing rows sit exactly at the threshold. Then document the detection table, the five states and what each means for the reviewer, the `lint` configuration key, and how to read a `failed` entry.
- [x] 4.2 [P4] [req: review-lint-step] Edit `plugins/s/skills/review/SKILL.md`: add a short `### 3b. Read the linter output` step after step 3 naming the `semdiff lint` invocation and stating that a linter finding is corroboration the reviewer weighs and reports only where it bears on the change, never promoted to a review finding automatically. Add a `linters.md` row to the `## References` table whose `Load when` cell satisfies the agreement test against task 4.1's sentence. The file is at 291 of its 300-line ceiling, so keep the inline step to roughly six lines and report the final count.
- [x] 5.1 [P5] [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json` to `0.6.218`, per the cache-snapshot rule in AGENTS.md.
- [x] 5.2 [P5] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` and confirm every test passes, task 1.1's module included. Then run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm no regression — a registry test asserts `RECOGNIZED_CONFIG_KEYS` and the example JSON agree in both directions, so task 2.2 must satisfy it. Report both counts.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 189 | 55.0k |
| Write | 2 | 39.6k |
| Edit | 12 | 27.4k |
| Read | 37 | 9.7k |
| (no tool) | 0 | 8.8k |
| Agent | 4 | 2.3k |
| ToolSearch | 4 | 766 |
| Monitor | 1 | 475 |
| TaskStop | 1 | 59 |
| **Total** | 250 | 144.0k |
