# Tasks

## 1. Help skill

- [x] 1.1 [req: usage-help-skill, usage-help-sources, usage-help-verdict, usage-help-oracle-route, usage-help-docs] Add `plugins/s/skills/build/tests/test_help_skill_contract.py`. Assert that the new `SKILL.md` and its harness body each name the three verdicts, `shipd --help`, `model memory`, and `/s:ask`. Assert that `SKILL.md` contains `plugin.json` and no `AskUserQuestion`, that `docs/help.md` exists, and that `docs/cheatsheet.md` and `AGENTS.md` each name `/s:help`. Run it and observe it fail.
- [x] 1.2 [req: harness-plan-mode-guard] In `plugins/s/skills/build/tests/test_plan_mode_guard_contract.py`, add `"help"` to `READ_ONLY` and change "read-only five" to "read-only six" in the docstring.
- [x] 1.3 [req: usage-help-skill, usage-help-sources, usage-help-verdict, usage-help-oracle-route] Write `plugins/s/skills/help/SKILL.md` following D2 to D6, with a folded `description: >-`. Sections in order: version announcement, read-only rules, route decisions, read the sources, answer. Name the sources as `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/bin/shipd --help`.
- [x] 1.4 [req: usage-help-skill, usage-help-sources, usage-help-verdict, usage-help-oracle-route] Write `plugins/s/harness/bodies/help.md` with the D6 one-liner in its `<!-- description: ... -->` line, the `<!-- include:preamble -->` line, and the same rules as numbered steps. Read skills from `"$S/../../"*/SKILL.md`, which is the installed `skills/` folder. Use no subagent branch.

## 2. Docs

- [x] 2.1 [req: usage-help-docs] Through `/s:document`, write `docs/help.md` (how-to): when to use it, how to run it, the three verdicts, and a link to `oracle.md`.
- [x] 2.2 [req: cheatsheet-page-links] In `docs/cheatsheet.md`, add the `/s:help <question>` row with one link, to `help.md`, after the `/s:gate` row. Add `s:help` after `s:onboard` in the "Spec, build, ship" list.
- [x] 2.3 [req: usage-help-docs] In `AGENTS.md`, add "`/s:help` to answer a how-to question about shipd" to the skill roll before `/s:teach`.

## 3. Ship

- [x] 3.1 [req: *] Bump the patch version in `plugins/s/.claude-plugin/plugin.json` above the version on the remote main branch.
- [x] 3.2 [req: *] Run `docs_lint.py` on `docs/help.md` and `docs/cheatsheet.md`. Run the unittest suite under `plugins/s/skills/build/tests` and confirm it ends `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 40 | 17.6k |
| SubagentHandback | 4 | 3.6k |
| Agent | 3 | 1.3k |
| SendMessage | 2 | 1.1k |
| ToolSearch | 2 | 684 |
| (no tool) | 0 | 538 |
| TaskStop | 1 | 310 |
| Monitor | 1 | 249 |
| Read | 1 | 125 |
| **Total** | 54 | 25.6k |
