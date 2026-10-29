## 1. Guard test

- [x] 1.1 [req: no-question-rejection-workaround] Add
      `plugins/s/skills/build/tests/test_no_rejection_recovery.py`, modelled on
      `plugins/s/skills/build/tests/test_harness_neutral_prose.py`: walk every
      `*.md` under `plugins/s/skills/` and `plugins/s/harness/` and fail on any
      line matching the case-insensitive regex
      `rejection[ -]recovery|rejected or interrupted`, listing every
      `path:line`. Add a second test asserting the regex flags
      "## Question rejection recovery" and "question-rejection-recovery".
      Run it with `python3 -B -m unittest` and observe the repository scan
      fail.

## 2. Skill sections

- [x] 2.1 [req: no-question-rejection-workaround] Delete the
      `## Question rejection recovery` section, from its heading through the
      line before the next heading, in the SKILL.md of autopilot, doctor,
      epic, fix, forget, gate, initiative, plan, prd, research, review,
      status, and worktree-hooks (all under `plugins/s/skills/`). Leave
      exactly one blank line between the preceding and following content.
- [x] 2.2 [req: no-question-rejection-workaround] Delete the
      `### Question rejection recovery` subsection in
      `plugins/s/skills/build/SKILL.md` the same way.
- [x] 2.3 [req: no-question-rejection-workaround] Delete the
      `**Question rejection recovery.**` list item and its continuation lines
      in `plugins/s/skills/epic-grill/SKILL.md`,
      `plugins/s/skills/onboard/SKILL.md`, and
      `plugins/s/skills/plan-deep/SKILL.md` (item `4.`).
- [x] 2.4 [req: remember-skill, git-backing-flow] In
      `plugins/s/skills/remember/SKILL.md`, replace "this skill's
      confirmation is a typed round, so it does not join the
      question-rejection-recovery roster." with "this skill's confirmation is
      a typed round.", and replace "— which keeps `/s:remember` off the
      question-rejection-recovery roster." with a full stop closing the bold
      sentence. Rewrap the two touched paragraphs.

## 3. Harness files

- [x] 3.1 [req: no-question-rejection-workaround] In
      `plugins/s/harness/bodies/ask.md`, `plugins/s/harness/bodies/forget.md`,
      and `plugins/s/harness/bodies/status.md`, delete the sentence that
      starts "Never treat a rejected or interrupted dialog" through "wait for
      a typed reply." and rewrap the paragraph.
- [x] 3.2 [req: no-question-rejection-workaround] In
      `plugins/s/harness/bodies/plan-deep.md`, delete the sentence "If a
      dialog is rejected, never treat it as an answer; re-offer the choices as
      a typed list." and rewrap the paragraph.
- [x] 3.3 [req: no-question-rejection-workaround] In
      `plugins/s/harness/references/forget.md`, delete the paragraph that
      starts "An interaction that comes back rejected or interrupted" and its
      following blank line.

## 3b. Question-brief roster floor

- [x] 3.4 [req: no-question-rejection-workaround] In
      `plugins/s/skills/build/tests/test_question_brief_contract.py`, change
      `test_roster_is_large_enough`'s floor from `21` to `14`: removing the
      rule took the only `AskUserQuestion` mention out of eight skills, so the
      computed roster now holds 14. Run that file with `python3 -B` and
      confirm OK.

## 4. Plugin version

- [x] 4.1 [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.353` to `0.6.354`.

## 5. Verify

- [x] 5.1 [req: *] Run `python3 -B -m unittest discover -s plugins/s/skills/build/tests`
      and `python3 -B -m unittest discover -s plugins/s/skills/document/tests`;
      grep each run's stderr for `OK` or `FAILED` and confirm both print `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 33 | 12.7k |
| SubagentHandback | 3 | 2.3k |
| Agent | 2 | 704 |
| (no tool) | 0 | 198 |
| SendMessage | 1 | 196 |
| **Total** | 39 | 16.1k |
