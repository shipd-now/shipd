# review-risk-lenses

- [x] 1.1 [P1] [req: review-risk-lenses] Extend `plugins/s/skills/review/tests/test_skill_references.py` with the assertions this change must satisfy, and confirm they FAIL before any other task is claimed. Add: all five trigger phrases (`secret`/`credential exposure`, `authorization boundary`, `unbounded work`, `resource release`, `migration reversibility`) appear in `SKILL.md` itself, not only in the References table or a reference file; `SKILL.md` states the exposure severity floor; `plugins/s/harness/bodies/review.md` and `plugins/s/integrations/copilot/SKILL.md` each name all five triggers and the floor; and `plugins/s/skills/review/references/json-output.md` lists `security`, `performance`, `stability`, `data-integrity` in the taxonomy enum. Do not weaken any existing assertion — `test_under_line_ceiling` and `test_table_cell_agrees_with_reference_condition` must keep their current strength.
- [x] 2.1 [P2] [req: review-risk-lenses] Create `plugins/s/skills/review/references/risk-lenses.md`. Open with the level-1 title `# Risk lenses` and, directly beneath it, a sentence stating the load condition in the form the agreement test requires — it must contain "reads this file" and share at least 3 content words of 4+ letters with the `Load when` cell task 3.1 writes. Then carry one section per trigger — secret or credential exposure, authorization boundary, unbounded work, resource release, migration reversibility — each giving what to look for in a diff, one worked example of a real finding, and one worked example of a reflex finding that is not worth reporting. State the exposure floor: the first two triggers always rate `high`.
- [x] 3.1 [P3] [req: review-risk-lenses] Edit `plugins/s/skills/review/SKILL.md`. Insert `### 5b. Risk lenses` between step 5 and step 6, holding one line per trigger in the order given in plan.md's Implementation, plus a sentence pointing at `${CLAUDE_PLUGIN_ROOT}/skills/review/references/risk-lenses.md` for depth. Add the exposure floor to the `**Severity rubric.**` block under step 6, as a rule beneath the three tier definitions. Add a fourth row to the `## References` table for `risk-lenses.md`, whose `Load when` cell must satisfy the agreement test against task 2.1's condition sentence — run that test rather than assuming the wording passes. Keep the file under 300 lines and report its final line count.
- [x] 3.2 [P3] [req: review-risk-lenses] Edit `plugins/s/skills/review/references/json-output.md` line 17, adding `security`, `performance`, `stability` and `data-integrity` to the `cohort` enum. Change nothing else in the file, and leave the field named `cohort` — the rename is the sibling change `review-finding-category`.
- [x] 3.3 [P3] [req: review-risk-lenses] Edit `plugins/s/harness/bodies/review.md`, adding a numbered step after its step 6 carrying all five triggers, condensed to the file's existing house style (a compact numbered paragraph, not a bullet list per trigger), and renumbering the steps that follow. Add the exposure floor to the severity definitions in its step 8. This file ships into other repositories and cannot read a reference file, so the guidance is inline and self-contained.
- [x] 3.4 [P3] [req: review-risk-lenses] Edit `plugins/s/integrations/copilot/SKILL.md`, adding a step after its step 4 carrying all five triggers in that file's house style, and renumbering `### 5. Report` accordingly. Add the exposure floor to the severity definitions at lines 171-175. This template is vendored byte-for-byte into user repositories and runs in GitHub Actions, so it must reference no file under `skills/review/references/`.
- [x] 4.1 [P4] [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json` to `0.6.216`, per the cache-snapshot rule in AGENTS.md.
- [x] 4.2 [P4] [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests -v` and confirm every test passes, task 1.1's new assertions included. Then run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm no regression — `test_copilot_verb.py` reads the vendored template that task 3.4 edits, and `test_harness_bodies.py` reads the body that task 3.3 edits.
- [x] 4.3 [P4] [req: *] Update the four `markdown_section(self.text, "### 5. Report")` locators in `plugins/s/skills/build/tests/test_copilot_verb.py` (lines 429, 443, 457, 478) to `"### 6. Report"`, matching the renumbering task 3.4 performed. The heading is a locator, not an assertion — each test checks the section's content (the ship/fix markers, `verdict line`, `own line`), so only the anchor changes. Weaken no assertion, and leave the `assertTrue(report.strip(), ...)` guard in place. Then re-run task 4.2's two suites.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 192 | 65.1k |
| Edit | 14 | 11.6k |
| (no tool) | 0 | 11.1k |
| Read | 12 | 5.0k |
| Agent | 4 | 1.9k |
| Write | 1 | 1.4k |
| SendMessage | 1 | 707 |
| ToolSearch | 4 | 295 |
| Monitor | 1 | 272 |
| **Total** | 229 | 97.4k |
