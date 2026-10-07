## 1. Raise the line ceiling before anything is added

- [x] 1.1 [req: review-skill-references] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 329 and `python3 -m unittest
      discover -s plugins/s/skills/review/tests` is green at 242 tests.
- [x] 1.2 [req: review-skill-references] In
      `plugins/s/skills/review/tests/test_skill_references.py`, raise
      `test_under_line_ceiling` from 330 to 350 and give it a docstring
      recording why: everything this change adds is a rule applied on every
      review, the detail that could be extracted already has been, and a
      measured defect showed an always-applies rule loses to the inline
      surface when deferred to a reference. Quote the precedent set when the
      harness body's ceiling went from 120 to 140 — a ceiling guards against
      bloat and is not a budget to compress real instructions into.
- [x] 1.3 [req: review-skill-references] Do not restate 350 anywhere else. The
      `review-skill-references` requirement owns the figure and says so in its
      own text. Grep the repository for the old figure and confirm no second
      owner appeared.

## 2. Generalise the location rule

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step 6,
      replace the parenthetical "the fix site, never a symptom" on the location
      field with the generalised rule: the primary location is the fix site —
      the line your own fix would change, never a symptom site in place of it —
      and a further location is added only where that site independently shows
      the defect on its own terms. Reuse the phrasing the same file already
      uses for a description-drift finding's further location, so the general
      rule and the special cases agree word for word rather than merely in
      spirit. Leave the recurring-defect sentence about the `locations` array
      intact.
- [x] 2.2 [req: review-risk-lenses] In
      `plugins/s/skills/review/references/risk-lenses.md`, reword the packaging
      lens's second-location guidance so it cites that general permission
      rather than reading as its own standalone exception: the import is named
      because it independently shows the omission, being the line that fails at
      run time. Do the same in the matching "Real finding" example. Add no new
      permission here — the rule now lives inline in SKILL.md.

## 3. Name concrete instances under the impact rule

- [x] 3.1 [req: review-skill] In the same file's step 6 rubric, extend the
      Impact rule bullet so the four abstract categories are followed by three
      concrete instances a reviewer can recognise: a success response that
      hides a failure — an empty result returned as if real while a count or
      flag says otherwise; a cleanup path that drops the record and leaves the
      data, or the reverse; and an error path that loses the only copy. Keep
      the four categories as the general rule; the instances sit beneath them,
      not instead of them.
- [x] 3.2 [req: review-skill] Keep the existing worked example about a
      swallowed error that loses a file, or fold it into the third instance,
      but do not drop it — it is the rule's only concrete illustration today
      and losing content to compression has already shipped twice.

## 4. Close the hole findings fall through

- [x] 4.1 [req: review-skill] In the same file's step 6, extend the closing
      sentence that currently covers being unsure between two levels so it
      also covers being unable to place a severity at all: never drop a finding
      because its severity is unclear — report it at the best estimate and say
      the estimate is uncertain. A defect you can describe is a defect you
      report.
- [x] 4.2 [req: review-skill] Do not touch the `low` bullet's definition, and
      name no defect kind under it. Rating `low` stays defined by contained
      impact. If the wording you reach for needs
      `LowBulletNamesNoKindTest` relaxed, it is the wrong wording — stop and
      report rather than relaxing the test.

## 5. Mirror onto the reference-free surfaces

- [x] 5.1 [req: review-skill] In `plugins/s/harness/bodies/review.md` numbered
      step 11, apply tasks 2.1, 3.1 and 4.1 to its own copies of the location
      sentence, the impact paragraph and the closing unsure sentence. This file
      ships into other repositories with no plugin root and can read no
      reference file, so every word it needs must be inline.
- [x] 5.2 [req: skill-template] In
      `plugins/s/integrations/copilot/SKILL.md`, apply tasks 3.1 and 4.1 only.
      Do not apply task 2.1: this template carries no fix-site or symptom rule
      to generalise, as plan.md records, so there is nothing for it to attach
      to and adding one would be new scope.
- [x] 5.3 [req: review-skill] Report the rendered line count of the review
      harness body against its ceiling of 140 by running `python3 -m unittest
      discover -s plugins/s/skills/build/tests -k
      test_every_body_stays_lean_at_the_full_vocabulary`, which must pass.

## 6. Pin the new rules with tests

- [x] 6.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add a test that
      the generalised further-location rule appears on both reference-free
      surfaces — `plugins/s/skills/review/SKILL.md` and
      `plugins/s/harness/bodies/review.md` — and that neither still states an
      unqualified prohibition on a symptom site. Guard the patterns against
      markdown emphasis with a character class such as `[*_\s]+` rather than a
      bare `\s+`.
- [x] 6.2 [req: review-skill] Add a test that each of the three concrete impact
      instances appears on all three rubric surfaces, including the copilot
      template. Assert on a distinctive phrase per instance rather than a whole
      sentence, so a later rewording does not break the test spuriously.
- [x] 6.3 [req: review-skill] Add a test that all three rubric surfaces state
      the no-drop rule. Give it a docstring recording the measurement that
      motivated it: edge-case findings fell from 8 to 2 over three rounds while
      test-coverage findings stayed flat, and because the medium rubric already
      names an unhandled edge case, a re-rating would have moved them up rather
      than away — so they were being dropped, not re-rated.
- [x] 6.4 [req: review-skill] Run the review suite and fix anything that
      breaks. Where a heading-scoped regex is needed, bound the heading with
      `[^\n]*\n` rather than `.*` under `re.DOTALL`, which makes the heading
      swallow the rest of the file.

## 7. Version and verification

- [x] 7.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.261` to `0.6.262`.
- [x] 7.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      242-test baseline, accounting for the tests group 6 adds.
- [x] 7.3 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs.log 2>&1;
      tail -4 /tmp/bs.log` — because its summary goes to stderr and a
      stdout-only pipe loses the result silently. Expect 3172 tests. Report the
      verdict line verbatim.
- [x] 7.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 7.5 [req: *] Report both ceilings as numbers: the line count of
      `plugins/s/skills/review/SKILL.md` against its new ceiling of 350, and
      the rendered review harness body against 140.
- [x] 7.6 [req: review-skill] Add no reflow to this change. The ceiling was
      raised precisely so no unrelated paragraph needs rewrapping, and an
      unnecessary rewrap makes a measured diff harder to attribute. Confirm by
      running a word-level diff of `plugins/s/skills/review/SKILL.md` against
      `HEAD` and reporting that every word change falls inside the location
      rule, the impact rule, or the closing severity sentence.
- [x] 7.7 [req: body-content] Raise the rendered-body ceiling from 140 to 160
      in `plugins/s/skills/build/tests/test_harness_bodies.py`'s
      `test_every_body_stays_lean_at_the_full_vocabulary`, and extend its
      docstring to record this occasion. The review body reached 139 of 140
      carrying this change, and the compression that bought the last line
      damaged meaning: "a cleanup dropping the record or the data" lost the
      orphaning the instance describes. The requirement's own words are the
      warrant — a ceiling guards against bloat and is not a budget to compress
      real instructions into.
- [x] 7.8 [req: review-skill] With that headroom, restore the three concrete
      instances in `plugins/s/harness/bodies/review.md` to say what they mean
      rather than what fits. The cleanup instance must carry that one of the
      pair is dropped while the other is left behind, in either direction —
      that leftover is the defect. Match the substance of the instances in
      `plugins/s/skills/review/SKILL.md`; terser phrasing is fine, lost
      meaning is not. Report the rendered line count afterwards.
- [x] 7.9 [req: review-skill] Lift the further-location rule out of the
      parenthetical it currently sits in, in `plugins/s/skills/review/SKILL.md`
      step 6, and give it its own sentence after the field list. A four-line
      parenthetical inside a list of fields is skimmed, and this change exists
      because a rule in the wrong place does not fire — burying it in an aside
      repeats that mistake in a smaller way. Keep the fix-site definition with
      the location field where it belongs.
