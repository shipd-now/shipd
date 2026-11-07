## 1. Contract test first

- [x] 1.1 [req: deliver-skill] In `plugins/s/skills/build/tests/test_autopilot_skill_contract.py`, rename `test_confirmation_is_the_last_question` to `test_the_run_asks_no_question`. Assert `"The run asks no question"` is in both `self.skill` and `self.body`, and assert neither contains `"Deliver one member first"` nor `"AskUserQuestion to confirm"`. Run `python3 -m unittest plugins/s/skills/build/tests/test_autopilot_skill_contract.py` and observe it fail.
- [x] 1.2 [req: in-session-park-and-continue] In the same file, add `test_no_confirmation_anchor_remains`: assert `"Phase 2 confirmation"` is absent from `self.skill` and `"launch confirmation"` is absent from `self.reference`, and `"Once the launch brief prints"` is present in both. Run it and observe it fail.

## 2. Skill

- [x] 2.1 [req: deliver-skill] In `plugins/s/skills/autopilot/SKILL.md`, rewrite the opening paragraph (lines 10-15): replace "confirm the run controls with the user" with "print the launch brief", and replace "after the confirmation you never ask one either" with "you never ask one either". Add the sentence "The run asks no question." to that paragraph.
- [x] 2.2 [req: deliver-skill] In the same file, change Phase 1 step 1's "stop here before the run controls are confirmed" to "stop here before the drive", and "carry every one of them into the Phase 2 confirmation brief" to "carry every one of them into the Phase 2 launch brief". In Mode selection, change "carry it through the confirmation in Phase 2" to "carry it through the launch brief in Phase 2".
- [x] 2.3 [req: deliver-skill] In the same file, replace the whole `## Phase 2 — Confirm the run controls` section with `## Phase 2 — Launch brief`. It states: the run controls come from the invocation (flags such as `--max-members 1`, or plain words such as "just the first spec" → `--max-members 1`, "serial" → `--parallel 1`); each unnamed control takes its default (keep the existing four-control bullet list with its defaults); the brief prints the mode, each resolved control marked `(invocation)` or `(default)`, the dry run's member list, every preflight `warn` line, and, for in-session runs, the `autopilot.py <epic> --waves --parallel N` output with its `blocked:` lines; the brief names the `dashboard.py tui --epic <epic>` live-view command (keep the existing code block); then the drive starts in the same turn. Close the section with: "The run asks no question: the skill issues no AskUserQuestion and no typed question round, and there is no cancel choice — not invoking the skill is the cancel."
- [x] 2.4 [req: deliver-skill] In the same file's in-session drive section, change "with `N` the `--parallel` value confirmed in Phase 2" to "with `N` the `--parallel` value the launch brief resolved". Directly after the `--waves --json` description paragraph, add: "Where the launch brief resolved `--max-members N`, drive at most N members, taken in the waves' order (wave by wave, member by member); list every other member as unreached in the run summary."
- [x] 2.5 [req: in-session-park-and-continue] In the same file's "Failure contract: park and continue" section, replace "After the Phase 2 confirmation, no human is present" with "Once the launch brief prints, no human is present". Replace "the confirmed `--timeout` seconds" with "the resolved `--timeout` seconds".
- [x] 2.6 [req: deliver-skill] In the same file's Phase 3, replace "Run the driver with the confirmed knobs" with "Run the driver with the resolved controls", and replace "surface them when confirming the run" with "surface them in the launch brief". Delete the closing "**Brief every question.**" paragraph at the end of the file.
- [x] 2.7 [req: deliver-skill] Run `grep -n -iE "confirm|AskUserQuestion|Cancel" plugins/s/skills/autopilot/SKILL.md`. Every remaining hit must be a prohibition ("issues no AskUserQuestion") or unrelated to the launch; reword any other hit with "launch brief" or "resolved".

## 3. Harness body and reference

- [x] 3.1 [req: deliver-skill] In `plugins/s/harness/bodies/autopilot.md`, change line 4's "confirm what the run may spend" to "print what the run may spend". Rename `## 2. Confirm the run controls` to `## 2. Launch brief`. Replace its first paragraph with: "The run spends real model time and opens real pull requests, so print a launch brief before driving: the mode, each control resolved from the invocation or its default, the dry run's member list, and every `warn` line. The run asks no question: start the drive in the same turn." Keep the controls table and the `--waves` paragraph. Delete the three-choice paragraph, the "Brief every question" paragraph, and the whole `<!-- if:question-dialogs -->` … `<!-- end -->` block. In section 1, change "carry every one of them into the confirmation" to "carry every one of them into the launch brief".
- [x] 3.2 [req: in-session-park-and-continue] In `plugins/s/harness/references/autopilot.md` line 134, replace "After the launch confirmation no human is present" with "Once the launch brief prints, no human is present". Grep that file for "confirm" and reword any launch-related hit the same way.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` from `0.6.366` to the next patch version above whatever `main` carries at build time.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and grep its output for `OK` or `FAILED`; every test, including tasks 1.1 and 1.2, must pass.
- [x] 4.3 [req: deliver-skill] In `plugins/s/skills/build/tests/test_question_brief_contract.py` `_roster()`, also `continue` when the SKILL.md text contains `"The run asks no question"`: such a skill names `AskUserQuestion` only to prohibit it, so it is not an asking skill. Update the module docstring to say so. Confirm `test_roster_is_large_enough` still passes, then re-run `python3 -m unittest discover -s plugins/s/skills/build/tests` and grep for `OK`/`FAILED`; it must be OK.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 51 | 16.4k |
| SubagentHandback | 5 | 5.7k |
| Monitor | 12 | 2.6k |
| Agent | 2 | 841 |
| (no tool) | 0 | 595 |
| SendMessage | 1 | 354 |
| ToolSearch | 2 | 213 |
| TaskStop | 1 | 57 |
| **Total** | 74 | 26.8k |
