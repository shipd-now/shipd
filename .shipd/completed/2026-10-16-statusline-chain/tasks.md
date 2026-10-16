# Tasks — statusline-chain

- [x] 1 [P1] [req: statusline-chain, statusline-integration, statusline-rendering] In `plugins/s/skills/build/tests/test_statusline.py`, add tests driving `statusline.sh` with `--then` and `--line`: a shipd workspace with `--then 'cat'` prints the `☕` line first and the session JSON after it; a non-shipd workspace with `--then 'echo theirs'` prints exactly `theirs`; no arguments renders `☕ <spec> · <bar> <pct>%` with no directory; `--line spec,directory` ends with the `~`-relative directory; `--line spec,context --line directory` prints two lines, the second the directory with no `☕`; `--line context,spec` begins `☕ █░░░ 25% · `; a missing `context_window` with no arguments prints `☕ <spec>` alone. Update existing tests that expected the directory on the default line. Then implement the argument loop, layout rendering, and `--then` chain in `plugins/s/integrations/statusline.sh` per `plan.md` `## Implementation` (bash 3.2 safe) and update its header comment. The file passes.
- [x] 2 [P1] [req: statusline-verb, doctor-verb, statusline-layout] In `plugins/s/skills/build/tests/test_shipd_cli.py`, replace the refuse-without-force test in `StatuslineVerbTest` with tests for: a foreign entry chained as `<cmd> --then '<existing>'` with `added statusline above existing statusline` and exit 0; `--force` replacing with `<cmd>` alone; an older shipd entry with a `--then` tail upgraded to `<cmd> --then '<tail>'` with exactly one occurrence of the statusline script path; a re-run leaving the file byte-identical; the bare report naming the above-it install. Add layout tests against a temp `--config` file: default renders `--line spec,context`; `--show directory` saves and renders `--line spec,context,directory`; `--hide context` removes it; `layout spec,context directory` saves two lines and re-registers keeping `--then`; bare `layout` prints the lines; an unknown or duplicate segment exits 2 writing nothing; a malformed `statusline` key exits 1. Add doctor tests: a foreign command warns naming it and `shipd statusline install`; a shipd command is `ok`. Then implement it all in `plugins/s/bin/shipd` per `plan.md`. All of `test_shipd_cli.py` passes.
- [x] 3 [P2] [req: statusline-verb, statusline-layout] Update the `statusline` row in `docs/cheatsheet.md` per `plan.md`, and bump `version` in `plugins/s/.claude-plugin/plugin.json` one patch above the version the main branch carries at build time.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 28 | 1.5k |
| Agent | 3 | 1.2k |
| SendMessage | 1 | 535 |
| (no tool) | 0 | 406 |
| Read | 2 | 240 |
| SubagentHandback | 4 | 84 |
| **Total** | 38 | 4.0k |
