## 1. Name the type and the response shape

- [x] 1.1 [req: review-skill] Confirm the starting point: the review suite is
      green at 288 tests, `plugins/s/skills/review/SKILL.md` is 374 lines
      against 400, and the rendered review harness body is 178 against 185.
- [x] 1.2 [req: review-skill] In
      `plugins/s/skills/review/references/verification.md`, name the spawn's
      `subagent_type` as `general-purpose` where it already names the `Agent`
      tool, and say why that type: it is a built-in, so it resolves in a
      headless session whether or not the plugin's own agent definitions load
      there, and an unresolvable type is indistinguishable from a denied spawn.
- [x] 1.3 [req: review-skill] In the same file, give the per-candidate verdict
      a concrete shape: one line per candidate, in the order received, carrying
      the candidate's index then either `confirmed` and a severity, or `killed`
      and a one-line reason. Show the two forms as a short literal block. State
      that the verdict carries no justification beyond that, and why — prompts
      demanding explanations raise misjudgment rates in code verification, and
      explanation belongs to the review's own prose.
- [x] 1.4 [req: review-skill] In the same file, state the handover: candidates
      travel inline in the spawn message with index, location, claim and why
      each was suspected; the diff is re-derived by the verifier running
      `semdiff diff` against endpoints the spawn message names. Say why the
      diff is re-derived rather than pasted — the verifier reads the change
      itself rather than the hunt's summary of it.

## 2. Mirror what the reference-free surface needs

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md`'s verify
      step, add the `subagent_type` name only. The response shape and the
      handover are detail and belong to the reference, which this step already
      points at.
- [x] 2.2 [req: review-skill] In `plugins/s/harness/bodies/review.md`'s verify
      step, add all three inline — the type, the response shape as a compact
      two-line form, and the handover — because that file can read no reference
      and anything omitted is gone for every repository that installs it. Keep
      it within seven lines. If it will not fit, stop and report rather than
      compressing: that file has lost content to compression three times.
- [x] 2.3 [req: review-skill] Report the rendered harness body's line count
      against 185.

## 3. Tests

- [x] 3.1 [req: review-skill] Add tests to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning that
      every surface stating the verify stage names a concrete `subagent_type`,
      and that the reference and the harness body both carry the
      one-line-per-candidate verdict shape. Guard patterns against markdown
      emphasis with a class such as `[*_\s]+`.
- [x] 3.2 [req: review-skill] Prove each new test fails against the
      pre-change text before trusting it, by checking its pattern against the
      merge-base copy of each file. Report which patterns you checked.

## 4. Version and verification

- [x] 4.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.269` to `0.6.270`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      288-test baseline.
- [x] 4.3 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs270.log 2>&1;
      tail -4 /tmp/bs270.log` — and report the verdict verbatim.
- [x] 4.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 4.5 [req: review-skill] Run a word-level diff of
      `plugins/s/skills/review/SKILL.md` against the merge base and confirm
      every word change falls inside the verify step. Add no reflow anywhere.
- [x] 4.6 [req: review-skill] Read the finished verify stage on both
      reference-free surfaces as a reviewer meeting it fresh, and answer one
      question: could two different sessions following this text produce
      verdict lines that a single parser would read differently? Quote the text
      you judged, not a conclusion. That ambiguity is the entire defect this
      change exists to remove.
- [x] 4.7 [req: body-content] Raise the rendered-body ceiling from 185 to 200
      in `plugins/s/skills/build/tests/test_harness_bodies.py`'s
      `test_every_body_stays_lean_at_the_full_vocabulary`, and record the
      reason honestly in its docstring: the review body reached 183 of 185
      carrying this change, leaving two lines, so the semantic review of this
      very pull request could not add a line to that file if it found one
      wanting. Also record what was checked and found false — the feature flags
      make no difference to this body's length, 183 lines with every feature on
      and every feature off, so 183 is not a worst case that typical installs
      undercut. It is the length every install renders.
      Note in the docstring that this is the third raise in three versions
      (140, then 160, then 185, now 200) and that a fourth should be a
      conversation about decomposing the body rather than another raise. A file
      that cannot defer anything to a reference has only two options when it
      grows, and raising the ceiling is the one that postpones the question.
      Do not restate 200 anywhere else — `body-content` owns the figure.
- [x] 4.8 [req: review-skill] Close the numbering ambiguity your own task 4.6
      found. Nowhere does any surface say whether the verdict line's `<index>`
      is zero-based or one-based, and both readings satisfy every stated
      instruction, so two sessions can emit `0 confirmed high` and
      `1 confirmed high` for the same first candidate. State on all three
      surfaces that the index is **zero-based and identical to the payload's
      `candidate` field**, so one numbering runs end to end. State it for the
      spawn message's candidate list too, since the ambiguity enters at the
      handover rather than only at the verdict. Add a test pinning that each
      surface says zero-based, and prove it fails against the current text.
- [x] 4.9 [req: body-content] The ceiling test checks the wrong case, and your
      registry check is what revealed it. `test_every_body_stays_lean_at_the_full_vocabulary`
      renders at the full feature vocabulary and gets 183, while a harness
      declaring no features renders 186 — because an absent feature emits
      fallback text that is longer than the gated version it replaces. So the
      worst case is the **minimal** vocabulary, and the test asserting leanness
      has been measuring the leanest render while its name claims otherwise.
      Extend it to render each entry in `harness_registry.HARNESSES` against
      that harness's own declared features and assert the ceiling for every
      one, keeping the full-vocabulary case as well. Report the highest number
      any registered harness produces. Rename nothing — a rename would hide
      which assertion changed.
- [x] 4.10 [req: body-content] Correct the stale line counts in
      `plugins/s/skills/build/tests/test_harness_bodies.py`'s ceiling docstring,
      and in this change's `plan.md` narrative if it repeats them. They read
      183 at the full vocabulary and 186 for the featureless harness; the
      current figures are **186** and **189**. The old numbers were measured
      before task 4.8 added the zero-based wording to the harness body, so they
      were accurate when taken and went stale three lines later. State the
      cause in one clause — that a count taken mid-build does not survive a
      later task editing the same file — so the next reader does not assume
      somebody measured carelessly. Verify both figures yourself at the end of
      your work rather than trusting these, since this task can go stale the
      same way.
