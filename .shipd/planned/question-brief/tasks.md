# Tasks

## 1. Contract test first

- [ ] 1.1 [req: question-brief] Create
      `plugins/s/skills/build/tests/test_question_brief_contract.py`,
      modeled on `test_epic_grill_contract.py`. Compute the roster: every
      `plugins/s/skills/*/SKILL.md` whose text contains `AskUserQuestion`,
      plus `plugins/s/harness/bodies/<skill>.md` for each that exists.
      Tests: the reference
      `plugins/s/skills/document/references/question-brief.md` exists, its
      first line is `<!-- doc-type: reference -->`, and it contains the
      headings "The four parts", "Where the brief goes", "Worked examples";
      every roster SKILL.md and body contains
      the substring "skills/document/references/question-brief.md"; the roster holds at
      least 21 skills. Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests -p "test_question_brief_contract.py"`
      and observe the tests fail.

## 2. The reference

- [ ] 2.1 [req: question-brief] Write
      `plugins/s/skills/document/references/question-brief.md` per plan.md's
      "The brief", "Placement", "The reference file", and "Worked examples"
      bullets. Add a "A bad question" section quoting the original
      room-cli-verb Q2 dialog and naming the three parts it lacked. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      plugins/s/skills/document/references/question-brief.md` until clean.
- [ ] 2.2 [req: question-brief] In
      `plugins/s/skills/document/SKILL.md`, add one line naming
      `plugins/s/skills/document/references/question-brief.md` as the rule for questions put to the
      user, beside its existing pointer to `plugins/s/skills/document/references/standard.md`.

## 3. Contracts that change shape

- [ ] 3.1 [req: epic-grill-final-round] In
      `plugins/s/skills/epic-grill/SKILL.md` "Final round", replace the
      AskUserQuestion-of-four bullet with: ask the whole agenda as one
      numbered typed round, each question opening with the brief from the
      reference, naming member(s) and `Q<n>`, default first marked
      "(Recommended)"; the user replies like "1a 2b". Change "one dialog" in
      "Amend and gate" and the re-check's further round to "one numbered
      typed round". Keep the rejection recovery bullet.
- [ ] 3.2 [req: epic-grill-final-round] In
      `plugins/s/harness/bodies/epic-grill.md` steps 5 and 6, add that each
      typed-round question opens with the brief from
      the substring "skills/document/references/question-brief.md".
- [ ] 3.3 [req: dialog-prose-separation] In
      `plugins/s/skills/epic/SKILL.md` and
      `plugins/s/skills/initiative/SKILL.md`, rename "The question contract
      (AskUserQuestion)" to "The question contract (typed round)" and change
      "Batch into one call" to one numbered typed round of 2–4 questions,
      each opening with its brief; fix every in-file reference to "a single
      AskUserQuestion" for that round (epic line ~252).
- [ ] 3.4 [req: dialog-prose-separation] In
      `plugins/s/skills/workspace/SKILL.md`, turn the `init` two-question
      AskUserQuestion (step at line ~111 and the "One call, two questions"
      bullet) and the member-by-member review (line ~321) into numbered
      typed rounds with a brief per question. Keep the `sync` and `map`
      single-question dialogs, and require their brief in the question text.

## 4. Pointers everywhere else

- [ ] 4.1 [req: question-brief] Add the pointer paragraph from plan.md's
      "The pointer" to every other roster SKILL.md: ask, autopilot, build,
      demo, doctor, drive, epic-grill, epic, fix, forget, gate, initiative,
      onboard, plan, prd, remember, research, review, status, workspace,
      worktree-hooks (skip any already given it in group 3). Place it
      directly above the question rejection recovery paragraph, or above
      the question contract where none exists.
- [ ] 4.2 [req: question-brief] Add the harness-body form of the pointer to
      `plugins/s/harness/bodies/<skill>.md` for the same 21 skills, beside
      where each body asks the user. Use no `AskUserQuestion`, `subagent`,
      or `sub-agent` token.

## 5. Verify

- [ ] 5.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from
      0.6.283 to 0.6.284.
- [ ] 5.2 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests` and grep the output for `OK` or
      `FAILED`; every test passes, including `test_harness_bodies.py`.
