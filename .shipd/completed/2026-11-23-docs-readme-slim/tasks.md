# Tasks — docs-readme-slim

Every task follows `plan.md` §Implementation. The README text comes from
`artefacts/readme-middle.md` in this change's directory; write no README
prose of your own.

## 1. Check the owner pages

- [x] 1.1 [req: *] Run `ls` on these sixteen files and confirm each exists:
      `docs/install.md`, `docs/getting-started.md`, `docs/core-ideas.md`,
      `docs/cheatsheet.md`, `docs/plan.md`, `docs/build.md`, `docs/epics.md`,
      `docs/semantic-review.md`, `docs/copilot-review.md`,
      `docs/multi-agent-pr.md`, `docs/oracle.md`, `docs/workspaces.md`,
      `docs/customise.md`, `docs/harnesses.md`,
      `docs/statusline-and-telemetry.md`, `docs/doctor.md`. Then confirm
      each `grep -c` prints 1 or more: `shipd vendor add` and `autoUpdate`
      in `docs/install.md`; `shipd harness add` in `docs/harnesses.md`;
      `shipd statusline install` and `builds.jsonl` in
      `docs/statusline-and-telemetry.md`; `shipd-now/shipd@` in
      `docs/copilot-review.md`; `rejected` in `docs/plan.md`; `/s:demo` in
      `docs/cheatsheet.md`. If any check fails, stop and report it; an
      earlier member has not merged, and no later task may run.

## 2. Drop the README from the registration tests

- [x] 2.1 [req: room-skill-docs, pr-callers] In
      `plugins/s/skills/room/tests/test_room_skill.py`
      (`test_registration_surfaces_name_the_skill`) and
      `plugins/s/skills/pr/tests/test_pr_skill.py`
      (`test_registrations_name_the_skill`), delete the `"README.md"` entry
      from the tuple the `for rel in (...)` loop walks. Leave `"AGENTS.md"`
      and the `docs/cheatsheet.md` entry.
- [x] 2.2 [req: init-skill-sections, drift-skill-registration] In
      `plugins/s/skills/build/tests/test_init_skill_contract.py`,
      `plugins/s/skills/build/tests/test_drift_skill_contract.py`, and
      `plugins/s/skills/build/tests/test_plan_deep_skill_contract.py`, in
      each file's `test_registry_files_mention_the_command`, delete the
      `"README.md"` entry from the tuple the loop walks. Leave the other two
      entries.
- [x] 2.3 [req: readme-docs-group-links] In
      `plugins/s/skills/build/tests/test_autopilot_skill_contract.py`,
      rename `test_readme_still_lists_the_autopilot_command` to
      `test_cheatsheet_lists_the_autopilot_command` and change its body to
      `self.assertIn("/s:autopilot", _read_repo("docs", "cheatsheet.md"))`.
- [x] 2.4 [req: room-skill-docs] Run
      `git show origin/main:plugins/s/.claude-plugin/plugin.json` and read
      its `version`. Set `version` in `plugins/s/.claude-plugin/plugin.json`
      to that value with the patch number raised by one.

## 3. Cut the README

- [x] 3.1 [req: readme-docs-group-links, readme-retains-onboarding-content, install-mode-docs, harness-mode-docs, pipeline-follower-docs, multi-agent-pr-entry-links]
      In `README.md`, delete every line from the line `## Install` up to,
      but not including, the line `## Structure`. In their place insert the
      full content of `artefacts/readme-middle.md`, unchanged. Leave lines
      1 to 12 (the icon and the intro) and everything from `## Structure`
      to the end of the file as they are.
- [x] 3.2 [req: readme-docs-group-links] In the `## Structure` tree of
      `README.md`, change the comment
      `# every other skill in the table above` to `# every other skill`.
      Change nothing else in the tree.
- [x] 3.3 [req: install-mode-docs] In `install.sh`, change line 2 from
      `# shipd installer — see README.md ("Install mode").` to
      `# shipd installer — see docs/install.md.`

## 4. Verify

- [x] 4.1 [req: document-registration, gate-skill-registration, fix-skill-registration, doctor-skill-registration, cheatsheet-doc]
      Confirm `docs/cheatsheet.md`'s `/s:` table holds one row each for
      `/s:document`, `/s:gate`, `/s:fix`, and `/s:doctor`, and that
      `AGENTS.md` names all four. Confirm the `venn-beta` fence in
      `docs/cheatsheet.md` names its three sets `Pipeline`, `Orchestration`,
      and `Memory`, in that order. Edit neither file; report a miss.
- [x] 4.2 [req: *] Confirm `wc -l README.md` prints 150 or fewer. Confirm
      `grep -n '^## ' README.md` prints exactly `## Install`,
      `## Documentation`, `## Structure`, `## Adding a command`,
      `## Adding a skill`, `## After editing`, in that order. Run
      `grep -nE 'autoUpdate|shipd update|shipd vendor|ln -s|shipd harness|harnesses\.json|autonomous-pipeline|^\|' README.md`
      and confirm no match. Confirm every relative link in `README.md`
      resolves to an existing file. Run
      `grep -rnE 'README\.md#|README\.md \("' docs plugins tools AGENTS.md install.sh .github --exclude-dir=retros`
      and confirm no match. Run `sh -n install.sh` and confirm exit 0.
- [x] 4.3 [req: *] Run
      `python3 -m unittest plugins/s/skills/room/tests/test_room_skill.py plugins/s/skills/pr/tests/test_pr_skill.py plugins/s/skills/build/tests/test_init_skill_contract.py plugins/s/skills/build/tests/test_drift_skill_contract.py plugins/s/skills/build/tests/test_plan_deep_skill_contract.py plugins/s/skills/build/tests/test_autopilot_skill_contract.py`
      and confirm it passes. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm it passes. Run the `Lint docs` step body from
      `.github/workflows/ci.yml` and confirm exit 0. Confirm
      `git status --short` lists only `README.md`, `install.sh`, the six
      test files, `plugin.json`, and this change's own artifacts. Run
      `plugins/s/bin/shipd lint docs-readme-slim` and confirm it reports the
      change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 91 | 61.2k |
| SubagentHandback | 3 | 18.3k |
| Agent | 3 | 2.7k |
| Read | 10 | 1.5k |
| Edit | 3 | 873 |
| SendMessage | 1 | 552 |
| (no tool) | 0 | 426 |
| ToolSearch | 2 | 340 |
| Monitor | 1 | 221 |
| **Total** | 114 | 86.1k |
