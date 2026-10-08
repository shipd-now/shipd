## 1. The reporting rubric returns to v0.6.260

- [x] 1.1 [req: review-skill] Confirm the starting point: the review suite is
      green at 293 tests, `plugins/s/skills/review/SKILL.md` is 377 lines
      against 400, and the worst rendered harness body is 194 against 250.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md`'s report
      step, replace the `low` bullet and the Impact rule with v0.6.260's
      reporting wording, recovered verbatim from commit `e360273`. The `low`
      bullet reads: a real but minor defect, naming swallowed errors, resource
      leaks on rare paths, dead or duplicated code, unread variables, unstable
      ids, and blocking calls in async contexts, and keeping "Pure style,
      naming, and formatting are never findings." Then v0.6.260's Impact floor
      bullet as it stood. Do not invent wording — `git show e360273:plugins/s/skills/review/SKILL.md`
      has both.
- [x] 1.3 [req: review-skill] Name that rubric for its job, so the two cannot
      be conflated later: it is the rubric for deciding what to report and
      proposing a severity, not for deciding the final one. Say in one clause
      that the verify stage owns the final severity and carries its own rubric.
- [x] 1.4 [req: review-skill] Keep the Exposure floor bullet in this rubric.
      State why in one clause: when the verifier does not run, every finding
      keeps the severity proposed here, so the one absolute in the rubric has
      to hold on this surface too.
- [x] 1.5 [req: review-skill] Do not touch the further-location rule, the
      recurring-defect rule, the breadth sweep, or the risk lenses. The
      further-location rule postdates v0.6.260 and is the one change measured
      reliable at 3 of 3 rounds; losing it to a careless revert is the specific
      risk in this task group.

## 2. The rating rubric moves to the verify stage

- [x] 2.1 [req: review-skill] In
      `plugins/s/skills/review/references/verification.md`, state the rating
      rubric in full: the `high` and `medium` definitions, the
      contained-impact `low`, the impact rule with its three concrete instances
      — a success response that hides a failure, a cleanup path that drops the
      record and leaves the data or the reverse, and an error path that loses
      the only copy — and the exposure floor.
- [x] 2.2 [req: review-skill] Change the spawn instruction in the same file so
      it quotes the **rating** rubric stated there, not the report step's
      rubric. The current text points at `SKILL.md` step 8; that pointer is now
      wrong and would hand the verifier the reporting rubric.
- [x] 2.3 [req: review-skill] State plainly in the same file that these are two
      rubrics with different jobs rather than two copies of one, and that
      neither may be duplicated. Re-aim the existing no-second-copy test
      instead of deleting it — see task 5.2.

## 3. Blind verification and the drift exception

- [x] 3.1 [req: review-skill] State in
      `plugins/s/skills/review/references/verification.md` that the spawn
      message carries no pull request title, description, or summary of either.
      Give the measured reason: a verifier handed the description killed a
      valid finding reasoning that the description made the cost intended.
- [x] 3.2 [req: review-skill] State that a `description-drift` candidate is
      verified in a separate spawn carrying the description and no diff,
      because such a candidate cannot be judged without it. Note that a single
      blind verifier would kill every drift candidate on principle, which is
      what happened before this change.
- [x] 3.3 [req: review-skill] State that the candidate list is in discovery
      order — the order the passes produced candidates. Replace the bare
      "deterministic" clause in
      `plugins/s/skills/review/references/json-output.md` and wherever else it
      appears, and say why severity order is excluded: it would correlate
      position with proposed severity and confound the clustering test the
      `candidate` field exists to support.

## 4. Mirror onto the reference-free surfaces

- [x] 4.1 [req: review-skill] `plugins/s/harness/bodies/review.md` carries both
      rubrics inline, since it can read no reference: the reporting rubric in
      its report step and the rating rubric in its verify step, each named for
      its job. Add the description ban, the drift spawn, and discovery order
      inline too.
- [x] 4.2 [req: review-skill] Apply the payload-side wording to
      `plugins/s/harness/references/review.md` so its machine-payload section
      agrees with `json-output.md` on discovery order.
- [x] 4.3 [req: review-skill] Report the worst rendered harness body across
      every registered harness against 250, measured at the end of your work.

## 5. Tests

- [x] 5.1 [req: review-skill] Add tests pinning: the reporting rubric defines
      `low` without a containment test; the rating rubric carries the three
      concrete instances; both rubrics carry the exposure floor; the spawn
      carries no title or description; drift candidates get their own spawn;
      and the candidate list is in discovery order. Guard patterns against
      markdown emphasis with a class such as `[*_\s]+`.
- [x] 5.2 [req: review-skill] Re-aim `NoRubricCopyInVerificationMdTest` rather
      than deleting it. Its premise was that the rating rubric lived only in
      the report step; now the rating rubric lives in `verification.md` by
      design. It should assert instead that neither rubric is duplicated — the
      reporting rubric's kind list does not appear in `verification.md`, and
      the rating rubric's concrete instances do not appear in the report step.
- [x] 5.3 [req: review-skill] Prove every absence assertion fails against the
      pre-change text before trusting it. Report which patterns you checked.

## 6. Version and verification

- [x] 6.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.272` to `0.6.273`.
- [x] 6.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      293-test baseline.
- [x] 6.3 [req: *] Run the build suite capturing stderr, and read the verdict
      with `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests" /tmp/bs273.log`.
      Do not use `tail` — this suite prints subprocess output after its own
      summary, so the verdict is not in the last lines.
- [x] 6.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 6.5 [req: review-skill] Confirm v0.6.263's further-location rule survives
      intact, by quoting it from the finished `SKILL.md`. It is the one change
      measured reliable at 3 of 3 rounds and the thing a revert most easily
      destroys.
- [x] 6.6 [req: review-skill] Read both finished rubrics as a stranger and
      answer one question: could a reviewer meeting them confuse which one
      applies at which stage? Quote the text you judged. If yes, that is the
      defect this change most plausibly introduces.
- [x] 6.7 [req: review-skill] Reduce the confusability your task 6.6 found,
      without touching the recovered v0.6.260 wording or the rating rubric's
      bullets. Three of the five bullets are byte-identical between the two
      rubrics and the distinguishing names differ by one word, so a skimming
      reader can read them as one rubric duplicated rather than two with
      different jobs. Add one orientation sentence immediately under each
      rubric's heading, stating what that rubric decides and that the other
      rubric exists and differs at the `low` bullet. Name the other rubric and
      where it lives. Do not rename `Impact floor` or `Impact rule` — both are
      load-bearing recovered or measured text — and do not reword any bullet.
- [x] 6.8 [req: review-skill] Add a test pinning that each rubric's orientation
      sentence names the other rubric, so the split cannot later be read as an
      accident. Prove it fails against the current text first.
