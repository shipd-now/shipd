## 1. Free SKILL.md's line budget by mechanical reflow

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 329, and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md`,
      mechanically reflow four bullet blocks at a wider column (~88, not a
      hard rule — just wider than their current wrap) by joining each
      bullet's existing wrapped lines into one string per bullet and
      rewrapping: step 3's five bullets (Callers/Treat/`--lang`/Changed
      constants/Uneven sibling sites), step 4's two bullets
      (Unreachable-guard/Comment-intent), step 5b's five risk-lens
      bullets, and step 6's four severity-rubric bullets
      (high/medium/low/Exposure floor). Change line breaks only — verify
      word-for-word against the original that nothing was reworded or
      dropped. In the step 5b reflow, the trigger name must stay exactly
      "secret or credential exposure" (not "secret/credential exposure") —
      `test_risk_lens_triggers_stated_inline` matches it as a literal
      phrase. Run `wc -l plugins/s/skills/review/SKILL.md` after; it should
      read at or below 325 (four blocks typically free 4-5 lines total,
      confirm the actual number here rather than assuming it).
- [x] 1.3 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm it is still green
      before adding anything new.

## 2. Add the PR-description check to SKILL.md

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`, insert
      between step `5c` and step `6` exactly:
      ```
      ### 5d. Check the PR description against the diff
      When a pull request's title and description are available, read
      `${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` and verify
      every claim against the diff.
      ```
- [x] 2.2 [req: review-skill] In the same file's `## References` table,
      add a row after the `new-code-checks.md` row:
      `| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` | a pull request's title and description are available |`
- [x] 2.3 [req: review-skill] Create
      `plugins/s/skills/review/references/pr-description.md` with exactly
      the content given in `plan.md`'s Implementation section (title,
      "reads this file when..." condition sentence, the claims-not-truth
      paragraph, and the four worked-example bullets).
- [x] 2.4 [req: review-skill] Run `wc -l
      plugins/s/skills/review/SKILL.md`; if it is at or above 330, trim
      task 1.2's reflow further (wider still, or reflow one more bullet
      block) — never by rewording the new step or dropping a reflowed
      block's words. Then run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm every test passes,
      including the new reference file's structural checks
      (`test_each_reference_opens_with_title_and_condition`,
      `test_table_cell_agrees_with_reference_condition`,
      `test_every_reference_file_is_named`,
      `test_every_named_reference_path_resolves`).

## 3. Mirror the check into the harness body

- [x] 3.1 [req: review-skill] Confirm the starting point: run
      ```
      python3 -c "
      import sys
      sys.path.insert(0, 'plugins/s/skills/build/tests')
      sys.path.insert(0, 'plugins/s/skills/build/scripts')
      import harness_bodies as hb, harness_registry as hr
      print(len(hb.render('review', hr.FEATURES,
                           refs_dir='plugins/s/skills/review/references').splitlines()))
      "
      ```
      and confirm it reports 119 (ceiling 120, zero slack).
- [x] 3.2 [req: review-skill] In `plugins/s/harness/bodies/review.md`,
      mechanically reflow step 1's prose and step 7's risk-lens paragraph
      at a wider column, same word-for-word-preserving technique as task
      1.2, with the same "secret or credential exposure" literal-phrase
      constraint. Tighten step 9's closing sentence as prose only if still
      short on budget after the reflow (merge "a real outcome, not a
      failure to force. Every unmet..." into one clause; keep every
      instruction). Re-run the render command from 3.1 after each change.
- [x] 3.3 [req: review-skill] Insert a new step after the existing step 9
      (spec verification) and before the existing step 10 (report),
      renumbering every step from 10 onward by one (10→11, 11→12, 12→13 —
      each stays two digits, so no indentation change is needed on the
      renumbered steps themselves). New step text, exactly:
      ```
      10. **Check the PR description against the diff when one is available —
          given inline, or via `gh pr view --json title,body`.** A title/body
          claim the diff contradicts or exceeds is its own finding, category
          `description-drift`, severity by the normal rubric.
      ```
- [x] 3.4 [req: review-skill] Re-run the render command from 3.1; it must
      report 119 or less. If it does not, reflow further per 3.2's
      technique (never reword the new step). Run `python3 -m unittest
      plugins.s.skills.build.tests.test_harness_bodies -v` and confirm all
      27 tests pass, including
      `test_every_body_stays_lean_at_the_full_vocabulary`.

## 4. The `description-drift` category

- [x] 4.1 [req: review-skill] In
      `plugins/s/skills/review/references/json-output.md`, append
      ` | "description-drift"` to the `"category":` enum line, and add one
      sentence after the existing `locations` array paragraph: "
      `description-drift` names a finding where a pull request's title or
      body makes a claim the diff contradicts, undersells, or oversells —
      present only when a pull request's title and description were
      available to review."
- [x] 4.2 [req: review-skill] Make the identical two edits to
      `plugins/s/harness/references/review.md` (its own `"category":` line
      and its own copy of the `locations` paragraph).
- [x] 4.3 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add
      `"description-drift"` to the `ALL_TAXONOMY_VALUES` frozenset and
      rename `test_value_set_contains_all_ten_values` to
      `test_value_set_contains_all_eleven_values` (body unchanged).
- [x] 4.4 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm every taxonomy-parity
      test passes, including
      `test_value_set_contains_all_eleven_values`,
      `test_value_sets_are_exactly_equal`, and
      `test_harness_reference_names_the_field_category`.

## 5. Fetch the description for a named PR review

- [x] 5.1 [req: review-skill] In
      `plugins/s/skills/review/references/posting.md` step 1, change
      `gh pr view <target> --json number,baseRefOid,headRefOid,url` to the
      same command with `,title,body` appended, and add one sentence
      after it: "`title` and `body` feed the PR-description check
      (`references/pr-description.md`) as claims to verify against the
      diff, never as resolution metadata."

## 6. Version and verification

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.252` to `0.6.253`.
- [x] 6.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-pr-description-check`), and confirm every suite
      and both lints pass, with both line-budget tests
      (`test_under_line_ceiling` and
      `test_every_body_stays_lean_at_the_full_vocabulary`) green.
