## 1. Restate the further-location rule inline

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 338, and `python3 -m unittest
      discover -s plugins/s/skills/review/tests` is green at 245 tests.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step 6,
      replace the further-location sentence. It currently reads that a further
      location is added "only where that site independently shows the defect on
      its own terms", and that wording excludes the run-time failure site it
      was written to permit. The new sentence names a site at which the defect
      is visible, as three alternatives: a line wrong in the same way, a line
      that shows the mismatch on its own terms, or the line at which the defect
      surfaces at run time even though that line is correct in isolation. Drop
      the word "only" — the list of shapes now carries the limit.
- [x] 1.3 [req: review-skill] Leave the primary-anchor sentence exactly as it
      is: the primary location is the fix site, never a symptom site in place
      of it. Only the further location gains the run-time shape, so nothing
      here reopens symptom anchoring. Confirm by reading the finished paragraph
      that a reviewer could not take it as permission to anchor a finding at a
      symptom.
- [x] 1.4 [req: review-skill] In `plugins/s/harness/bodies/review.md` step 11,
      apply the same change to its own terser copy, which currently reads "a
      further site only where it independently shows the defect". Keep all
      three shapes. This file ships into other repositories and can read no
      reference file, so a shape dropped here is gone for every repository that
      installs it. Terser phrasing is fine; a missing alternative is not.

## 2. Correct the packaging justification

- [x] 2.1 [req: review-risk-lenses] In
      `plugins/s/skills/review/references/risk-lenses.md`, the packaging lens
      currently justifies the import as a further location by saying it
      independently shows the omission. That claim is false — the import is
      correct code, and asserting otherwise is what made the general rule and
      this lens disagree. Reword it to say the import is the line at which the
      omission surfaces at run time, and that it qualifies under that shape
      rather than by being wrong on its own terms. Apply the same correction to
      the matching worked example.
- [x] 2.2 [req: review-risk-lenses] Keep the lens citing the skill's general
      permission rather than granting its own. That part of the previous
      version was right and is what stops the two rules drifting apart again.

## 3. Pin the run-time shape

- [x] 3.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, extend the test
      that pins the generalised location rule so it also requires the run-time
      shape on both reference-free surfaces — `plugins/s/skills/review/SKILL.md`
      and `plugins/s/harness/bodies/review.md`. Assert on the run-time idea
      rather than a whole sentence, so a later rewording does not break it
      spuriously. Guard the pattern against markdown emphasis with a character
      class such as `[*_\s]+` rather than a bare `\s+`.
- [x] 3.2 [req: review-skill] Give that test a docstring recording why the
      shape is pinned: the earlier wording required a further location to show
      the defect on its own terms, which a correct import never does, and the
      pg-pool second location fell from 1 of 3 rounds to 0 of 3 as a result.
- [x] 3.3 [req: review-skill] Add an assertion that neither surface still
      states the exclusive form — that a further location is added *only* where
      the site independently shows the defect. That exclusivity is the specific
      wording that caused the regression, so its absence is worth pinning
      directly rather than inferring from the presence of the new text.

## 4. Version and verification

- [x] 4.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.262` to `0.6.263`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      245-test baseline.
- [x] 4.3 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs263.log 2>&1;
      tail -4 /tmp/bs263.log` — because its summary goes to stderr and a
      stdout-only pipe loses the verdict silently. Expect 3172 tests. Report
      the verdict line verbatim.
- [x] 4.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 4.5 [req: *] Report both ceilings as numbers: `plugins/s/skills/review/SKILL.md`
      against 350, and the rendered review harness body against 160. Neither
      ceiling changes in this change and neither should come close.
- [x] 4.6 [req: review-skill] Add no reflow. Confirm with a word-level diff of
      `plugins/s/skills/review/SKILL.md` against `HEAD` that every word change
      falls inside the further-location sentence, and report the result.
