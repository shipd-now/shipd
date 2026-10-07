## 1. Move the kinds list out of the low rubric

- [x] 1.1 [req: review-skill] Confirm the starting point: `python3 -m unittest
      discover -s plugins/s/skills/review/tests` is green, `wc -l
      plugins/s/skills/review/SKILL.md` reports 327, and `python3 -m unittest
      discover -s plugins/s/skills/build/tests -k
      test_every_body_stays_lean_at_the_full_vocabulary` passes. Record the
      rendered line count of the review harness body by running
      `plugins/s/harness/bodies/review.md` through the same render the test
      uses; it should be 134.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, retitle
      step 5c from "Breadth sweep for minor defects" to "Breadth sweep" and
      rewrite its body so the step names the defect kinds itself rather than
      pointing at the rubric: a swallowed or silently-dropped error, a resource
      or file leak on a rare or cleanup path, dead or duplicated code, a field
      or variable declared but never read, an unstable or incorrect identity
      such as a list key derived from an array index, and a blocking call in an
      async context. Keep the existing "end to end" phrasing and the statement
      that the sweep catches what the structural and signature-chasing passes
      do not. Close the step by sending the rating to step 6's rubric. Do not
      call the kinds minor anywhere in the step.
- [x] 1.3 [req: review-skill] In the same file's step 6 severity rubric,
      replace the `low` bullet's kind list with a definition by impact: a real
      defect whose impact is contained, nothing lost, corrupted, exposed, or
      promised and unmet. Keep the sentence "Pure style, naming, and formatting
      are never findings" in the bullet verbatim.
- [x] 1.4 [req: review-skill] Replace the "Impact floor" bullet in the same
      rubric with the restated rating rule decided in plan.md: rate every
      finding by what the defect does rather than by the kind of defect it is,
      and data loss, data corruption, a security exposure, or a broken
      guarantee is `medium` or `high` however minor the kind looks, with the
      worked example that an error swallowed on a path that loses a file is not
      low. Remove the retired clause that says the low list names kinds of
      defect rather than severities — the list is no longer under `low`, so
      that clause would point at nothing. Leave the Exposure floor bullet, the
      `high` and `medium` bullets, and the blocks/never-blocks sentence
      untouched.

## 2. Clear the line ceiling by mechanical reflow

- [x] 2.1 [req: review-skill] Measure `wc -l
      plugins/s/skills/review/SKILL.md` after task 1. If it is 330 or more,
      free the shortfall by rewrapping prose blocks at 88 columns, which is the
      file's existing body convention. Take the measured candidates in order:
      the block at lines 65-73 rewraps from 9 lines to 7, and the block at
      lines 120-122 rewraps from 3 to 2. Four further single-line candidates
      exist near lines 173-176, 208-212 and 284-289 if more is needed. Never
      rewrap the YAML frontmatter at the top of the file: it is a folded scalar
      carrying the skill's description and trigger phrases.
- [x] 2.2 [req: review-skill] Prove each reflow preserved every word. For each
      block you rewrapped, extract the word sequence before and after your edit
      and compare them for exact equality — a reflow that drops, adds, or
      reorders a word is a content regression, which has already shipped twice
      from edits that looked harmless. Report the comparison result. If any
      block fails, restore it and rewrap a different candidate.
- [x] 2.3 [req: review-skill] Confirm `wc -l
      plugins/s/skills/review/SKILL.md` is under 330 and that `python3 -m
      unittest plugins.s.skills.review.tests.test_skill_references` collects
      and runs. Do not proceed while the ceiling is breached.

## 3. Mirror both changes on the reference-free harness body

- [x] 3.1 [req: review-skill] In `plugins/s/harness/bodies/review.md`, retitle
      numbered step 8 from "Breadth sweep for minor defects" to "Breadth sweep"
      and move the kind list into that step, matching task 1.2's content. This
      file ships into other repositories with no plugin root, so it can read no
      reference file and every word it needs must stay inline.
- [x] 3.2 [req: review-skill] In the same file's numbered step 11 rubric, apply
      task 1.3 and 1.4's changes to its own copy of the `low` bullet and its
      own copy of the impact paragraph. Keep its exposure-floor sentence, its
      effort-score and verdict lines, and its closing unsure-between-two-levels
      sentence untouched.
- [x] 3.3 [req: review-skill] Confirm the rendered body stays under its
      ceiling: `python3 -m unittest discover -s plugins/s/skills/build/tests -k
      test_every_body_stays_lean_at_the_full_vocabulary` must pass, and report
      the rendered line count as a number.

## 4. Name the import site on a file-not-shipped finding

- [x] 4.1 [req: review-risk-lenses] In
      `plugins/s/skills/review/references/risk-lenses.md`, extend the packaging
      lens's "Does a new file actually ship?" question so it states that the
      finding anchors at the manifest, the line a fix would change, and names
      the importing line as a further location because that is where the
      omission breaks at run time. Make the same point concrete in the matching
      "Real finding" example about the omitted module, which already names both
      the manifest and the entry point that requires it.
- [x] 4.2 [req: review-risk-lenses] Verify this does not contradict the
      fix-site rule stated in `plugins/s/skills/review/SKILL.md`: the manifest
      stays the primary anchor and the import is an additional location on the
      same finding. Report the sentence you checked it against.

## 5. Bring the copilot template's rubric in line

- [x] 5.1 [req: skill-template] In
      `plugins/s/integrations/copilot/SKILL.md`, replace the severity rubric's
      `low` bullet — currently "style, naming, minor redundancy, defensive
      nits" — with the same definition by impact used on the other two
      surfaces: a real defect whose impact is contained, and pure style, naming
      and formatting are never findings at any severity. This bullet currently
      states the opposite of the other surfaces, making style reportable at
      `low`, so read it as a contradiction to remove rather than wording to
      refresh.
- [x] 5.2 [req: skill-template] Add the rating rule beside that rubric in the
      same file, matching task 1.4's content: severity follows what the defect
      does rather than the kind of defect it is, and data loss, data
      corruption, a security exposure, or a broken guarantee is `medium` or
      `high`. Leave the existing exposure sentence and the verdict rule below
      it untouched. Add no kinds list and no breadth-sweep step — this template
      has no sweep, which plan.md records as a deliberate non-goal.
- [x] 5.3 [req: skill-template] Confirm the template's ownership marker line
      and its frontmatter are unchanged, and that no other rubric or verdict
      text in the file moved.

## 6. Re-aim the tests on the new structure

- [x] 6.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, re-aim
      `_IMPACT_FLOOR_PATTERNS` at the restated rating rule. The retired proxy
      matching "kinds of defect, not severities" must go, since the wording it
      proxied for is gone; replace it with a proxy for rating by what the
      defect does rather than the kind it is. Keep the second pattern's intent,
      that data loss reaches medium or high. Add
      `plugins/s/integrations/copilot/SKILL.md` to
      `ImpactFloorParityTest`'s loop over rubric surfaces and delete the
      docstring paragraph excluding it as a tracked inconsistency — the
      template now carries the rule, and the widened loop is what stops it
      drifting back. Update the comment above the
      tuple, and `ImpactFloorParityTest`'s docstring, to describe the new
      structure rather than the old floor. Guard both patterns against markdown
      emphasis with a character class such as `[*_\s]+`, never a bare `\s+`.
- [x] 6.2 [req: review-skill] Rewrite
      `test_breadth_sweep_points_at_the_rubric_categories` rather than deleting
      it — this change inverts its premise, so the assertion has to invert with
      it. Rename it to match what it now checks, keep its "end to end"
      assertion, and assert instead that step 5c names at least a
      representative set of the defect kinds itself. Keep the heading pattern
      bounded with `[^\n]*\n` rather than `.*` under `re.DOTALL`, which would
      make the heading swallow the rest of the file.
- [x] 6.3 [req: review-skill] Add a test asserting the other half of the
      change: the `low` bullet of step 6's severity rubric in
      `plugins/s/skills/review/SKILL.md` names none of the moved defect kinds,
      and neither do the matching rubric bullets in
      `plugins/s/harness/bodies/review.md` and
      `plugins/s/integrations/copilot/SKILL.md`. Scope the assertion to the
      `low` bullet, not to the whole file — the kinds legitimately appear
      elsewhere, in the breadth-sweep step. Assert for the copilot template
      that its `low` bullet no longer names style, naming, redundancy, or
      nits, since that is the contradiction task 5.1 removed. Give the test a
      docstring recording that the kinds under the low heading are what made
      the floor lose, measured on a benchmark run.
- [x] 6.4 [req: review-skill] Check every other assertion in that file that
      names the old wording and update any that break. Candidates are the
      helper `_impact_floor_stated`, anything matching the word "minor", and
      any literal-phrase check over the step 5c or rubric text. Run the file's
      suite and fix what fails.

## 7. Version and verification

- [x] 7.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.260` to `0.6.261`.
- [x] 7.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and confirm both suites pass. Report
      the review suite's test count against its 239-test baseline, accounting
      for the test task 6.3 adds.
- [x] 7.3 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name, and confirm both exit 0.
- [x] 7.4 [req: *] Report both ceilings as numbers: the line count of
      `plugins/s/skills/review/SKILL.md` against 330, and the rendered line
      count of `plugins/s/harness/bodies/review.md` against 140.
- [x] 7.5 [req: review-skill] Read the final breadth-sweep step and severity
      rubric on all three surfaces end to end, as a reviewer meets them, and
      confirm nothing left in any of them calls the defect kinds minor or low
      before severity is assigned. That residual framing is the whole defect
      this change exists to remove, so a leftover instance would ship the bug
      again.
- [x] 7.6 [req: review-skill] Remove the severity pre-assignment the
      read-through found at `plugins/s/skills/review/SKILL.md` step 4, which
      reads "Both are usually low severity alone, but they compound". It
      assigns a severity by kind — the unreachable guard and the comment
      mismatch — before step 6 rates anything, which is the defect class this
      whole change removes, and it contradicts this change's own requirement
      that the skill rate every finding by what the defect does rather than by
      the kind of defect it is. Keep the compounding observation, which is
      real information, and drop the severity label: state that either alone
      often looks small, that together they compound, and that both are rated
      at step 6 by what they actually do. Re-measure the file against the 330
      ceiling afterwards and report the number.
