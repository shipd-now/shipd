## 1. Contract tests first

- [ ] 1.1 [req: plan-deep-rubric, epic-risk-rubric-ratings] In `plugins/s/skills/build/tests/test_plan_deep_skill_contract.py`, change `RUBRIC` to `os.path.join(SKILLS_DIR, "epic", "references", "risk-rubric.md")`, and replace `"skills/plan-deep/references/rubric.md"` in the required-token tuple with `"skills/epic/references/risk-rubric.md"`. Update the module docstring's path wording to match. Add `test_old_rubric_path_is_gone`, asserting `os.path.join(SKILLS_DIR, "plan-deep", "references", "rubric.md")` does not exist. Add `test_epic_cites_the_rubric`, asserting that `plugins/s/skills/epic/SKILL.md` and the whitespace-normalized `plugins/s/harness/bodies/epic.md` each contain the string "skills/epic/references/risk-rubric.md". Run the file and see it fail.
- [ ] 1.2 [req: epic-grill-risk-report] In `plugins/s/skills/build/tests/test_epic_grill_contract.py` `test_ending_prints_the_risk_report_and_plan_deep_offer`, replace `"skills/plan-deep/references/rubric.md"` with `"skills/epic/references/risk-rubric.md"`. Run the file and see it fail.

## 2. Move the rubric

- [ ] 2.1 [req: plan-deep-rubric] Run `git mv plugins/s/skills/plan-deep/references/rubric.md plugins/s/skills/epic/references/risk-rubric.md`. Then remove the now-empty `plugins/s/skills/plan-deep/references` directory if git left it on disk.
- [ ] 2.2 [req: plan-deep-rubric] In `plugins/s/skills/epic/references/risk-rubric.md`, replace the opening paragraph's first two sentences with: "The one risk rubric `/s:epic`, `/s:epic-grill`, and `/s:plan-deep` share. All three load it from the string "skills/epic/references/risk-rubric.md"; none restates the scale." After the Axes table, add one sentence: "`/s:epic` uses only this Axes table, for its four stub rating cells; the rest scores a written plan." Change nothing else.

## 3. Point the citers at the new path

- [ ] 3.1 [req: plan-deep-rubric] In `plugins/s/skills/plan-deep/SKILL.md` (line 30) and `plugins/s/harness/bodies/plan-deep.md` (line 22), replace the string "skills/plan-deep/references/rubric.md" with the string "skills/epic/references/risk-rubric.md".
- [ ] 3.2 [req: epic-grill-risk-report] In `plugins/s/skills/epic-grill/SKILL.md` (line 247) and `plugins/s/harness/bodies/epic-grill.md` (line 82), replace the string "skills/plan-deep/references/rubric.md" with the string "skills/epic/references/risk-rubric.md".
- [ ] 3.3 [req: epic-risk-rubric-ratings] In `plugins/s/skills/epic/SKILL.md` lines 426-427, replace "your honest per-change complexity estimate." with "rated by the Axes table in `${CLAUDE_PLUGIN_ROOT}/skills/epic/references/risk-rubric.md` (load it before writing the table)." In `plugins/s/harness/bodies/epic.md` lines 91-92, replace "your honest `low`, `medium`, or `high` rating in each of the four complexity columns" with "a `low`, `medium`, or `high` rating in each of the four complexity columns, rated by the Axes table in the string "skills/epic/references/risk-rubric.md"". Rewrap only the touched lines.
- [ ] 3.4 [req: *] Run `git grep -n "plan-deep/references/rubric" -- plugins` and confirm it prints nothing.

## 4. Version and verify

- [ ] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from `0.6.347` to `0.6.348`.
- [ ] 4.2 [req: *] Clear `__pycache__` under `plugins/`, run `python3 -B -m unittest discover -s plugins/s/skills/build/tests`, and confirm the summary reads `OK` (grep for `OK` or `FAILED`; unittest writes it to stderr).
