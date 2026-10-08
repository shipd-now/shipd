## 1. Raise the harness ceiling first

- [x] 1.1 [req: body-content] Confirm the starting point: the rendered review
      harness body is 159 lines against 160, `plugins/s/skills/review/SKILL.md`
      is 357 against 370, and the review suite is green at 275 tests.
- [x] 1.2 [req: body-content] Raise the ceiling in
      `plugins/s/skills/build/tests/test_harness_bodies.py`'s
      `test_every_body_stays_lean_at_the_full_vocabulary` from 160 to 185, and
      extend its docstring with this occasion: the verify stage must be inline
      on a file that can read no reference, and the body stood at 159 of 160
      with no room. Do not restate 185 anywhere else — `body-content` owns it.

## 2. The verify stage on SKILL.md

- [x] 2.1 [req: review-skill] Add a verify step to
      `plugins/s/skills/review/SKILL.md` between the new-code judgement step
      and the report step. Inline it states: what the stage does, that the
      verifier is spawned with the `Agent` tool and gets fresh context, that it
      returns confirm-with-severity or kill-with-reason per candidate, and that
      severity is the verifier's. Keep it to a short summary — the detail goes
      to the reference in task 2.2.
- [x] 2.2 [req: review-skill-references] Create
      `plugins/s/skills/review/references/verification.md`. It opens with a
      level-1 title and states its own load condition, like its eight siblings.
      It carries: what the verifier is given and deliberately not given; the
      per-candidate verdict shape; that it must not receive the reasoning that
      produced the candidates, and why cold start is the point; how severity is
      assigned; and the degradation path when the spawn is denied. Add it as a
      row to the References table in `SKILL.md`.
- [x] 2.3 [req: review-skill] Renumber every step after the insertion on
      `SKILL.md`, and fix every cross-reference that names a step by number.
      Several passes point at the rubric and the report by number. A stale
      pointer is a silent break, and this file has had one before.

## 3. Kills and verifier state in the payload

- [x] 3.1 [req: review-skill] In
      `plugins/s/skills/review/references/json-output.md`, specify a top-level
      `killed` array of objects carrying `location`, `what` and `reason`, and a
      top-level `verifier` object carrying `state` of `ran` or `skipped` plus a
      `reason` when skipped.
- [x] 3.2 [req: review-skill] State plainly in the same file that a killed
      candidate never appears among `findings`, under any status or flag. A
      consumer scoring the payload counts every `findings` entry as reported, so
      a kill placed there would erase the precision this stage exists to
      produce.
- [x] 3.3 [req: review-skill] Specify that the rendered report names the kill
      count, so a human reading the review sees what was removed rather than
      only what survived.

## 4. Degradation when the spawn is unavailable

- [x] 4.1 [req: review-skill] Specify on both reference-free surfaces that an
      unavailable or failing `Agent` spawn does not abort the review: record
      `verifier.state` as `skipped` with the reason, keep each finding's
      proposed severity, and add an entry to the report's explicit list of what
      could not be verified. Match the wording style the skill already uses for
      a failed difftastic probe and a failed base fetch.
- [x] 4.2 [req: review-skill] State that a review whose verifier did not run is
      never reported as verified. This is the whole reason the state field
      exists: a benchmark round or a headless user with a restricted tool list
      must be able to tell a verified review from an unverified one.

## 5. Mirror onto the harness body

- [x] 5.1 [req: review-skill] Add the verify stage to
      `plugins/s/harness/bodies/review.md` with its substance inline — the
      `Agent` spawn, fresh context, the per-candidate verdict, severity
      ownership, the `killed` array, the `verifier` state, and the degradation
      path. This file ships into other repositories and can read no reference
      file, so anything omitted here is gone for every repository that installs
      it.
- [x] 5.2 [req: review-skill] Renumber its steps and check the continuation
      indent: a two-digit list marker needs four spaces, and a stale three-space
      indent has silently broken markdown in this file before. Report the
      rendered line count against the new 185 ceiling.

## 6. Tests

- [x] 6.1 [req: review-skill] Add tests to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning that both
      reference-free surfaces name the verify stage, the `Agent` tool, fresh
      context, the `killed` array, the `verifier` state field, and the
      degradation path. Guard patterns against markdown emphasis with a class
      such as `[*_\s]+`, and bound any heading-scoped regex with `[^\n]*\n`
      rather than `.*` under `re.DOTALL`.
- [x] 6.2 [req: review-skill] Add a test that neither surface permits a killed
      candidate inside `findings` — assert the prohibition is stated, since the
      payload shape itself is prose here rather than code.
- [x] 6.3 [req: review-skill-references] Add
      `plugins/s/skills/review/references/verification.md` to whatever existing
      test enumerates the reference files and asserts each opens with a title
      and its load condition, rather than writing a new bespoke test.
- [x] 6.4 [req: review-skill] For every test asserting something is absent or
      prohibited, prove it fails against the pre-change text before trusting
      it. Two tests in this series passed vacuously because nobody checked they
      could fail.

## 7. Version and verification

- [x] 7.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.267` to `0.6.268`.
- [x] 7.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      275-test baseline.
- [x] 7.3 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs268.log 2>&1;
      tail -4 /tmp/bs268.log` — and report the verdict verbatim.
- [x] 7.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 7.5 [req: *] Report both ceilings as numbers: `SKILL.md` against 370 and
      the rendered review harness body against 185.
- [x] 7.6 [req: review-skill] Read the finished verify stage on both surfaces
      as a reviewer meeting it fresh, and confirm three things a benchmark
      depends on: the `Agent` tool is named by that exact name so a restricted
      runner can allow it; a denied spawn cannot pass silently; and a killed
      candidate cannot reach `findings`. Report what you read, not that you
      checked.
- [x] 3.4 [req: review-skill] Give each `killed` entry a `candidate` field
      holding its zero-based position in the candidate list the verifier
      received, and give the top-level `verifier` object a `candidates` field
      holding that list's total length. Specify both in
      `plugins/s/skills/review/references/json-output.md` alongside the rest of
      the payload, and state why they exist: surviving findings and kills are
      reported in separate arrays, so without a position and a total a reader
      cannot tell whether kills cluster by order in the list rather than by the
      merits of each candidate. That distinction decides whether one verifier
      per review is sufficient or whether candidates anchor on each other
      inside a single pass.
- [x] 3.5 [req: review-skill] State in the same file that the candidate list's
      order must be deterministic for a given review, since a position is
      meaningless against an order that varies between runs over the same
      diff.
- [x] 7.7 [req: review-skill-references] Raise the `SKILL.md` ceiling from 370
      to 400 in `plugins/s/skills/review/tests/test_skill_references.py`'s
      `test_under_line_ceiling`, and extend its docstring with the reason: the
      verify stage brought the file to 369 of 370, leaving one line, so the
      review gate on this very pull request could not add a line to `SKILL.md`
      if it found one wanting. A ceiling that blocks its own change's review is
      a trap rather than a guardrail. Do not restate 400 anywhere else —
      `review-skill-references` owns the figure and says so in its own text.
      The spec delta has already been updated; this task changes the test to
      match it.
- [x] 7.8 [req: review-skill] `plugins/s/harness/references/review.md` carries
      its own `## The machine payload` section with the full JSON object, and it
      does not mention `killed` or `verifier`. The harness body now tells a
      reviewer to emit both, so a harness-installed review is handed
      contradictory guidance: emit these fields, against a payload shape that
      has no place for them. Add `killed` and `verifier` to that object,
      matching the shape in
      `plugins/s/skills/review/references/json-output.md`, including the
      `candidate` position and the `candidates` total, and state there too that
      a killed candidate never appears among `findings`. This file was missing
      from the plan's file list — that was my omission, not a scope question.
- [x] 7.9 [req: review-skill] Revert the three mechanical rewraps in
      `plugins/s/skills/review/SKILL.md` to their merge-base text at
      `a7fe8f4`. They were done to fit under the old 370 ceiling, which has
      since risen to 400 with the file at 369, so none of them is needed. Two
      reasons to undo them: unrelated rewrap is noise in a diff a benchmark
      peer reads line by line, and the rewrap was not purely mechanical — a
      word-level diff against the merge base shows `the` and `value` dropped
      from "the severity value stays `medium`". That is a rewording inside an
      edit reported as content-preserving, which is exactly the failure that
      has shipped three times in this series. Restore the original wording,
      then re-run the word-level diff and report that the only remaining
      deletions are the renumbering ones.
