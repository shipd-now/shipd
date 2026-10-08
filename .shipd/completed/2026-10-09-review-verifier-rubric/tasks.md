## 1. The spawn carries the rubric

- [x] 1.1 [req: review-skill] Confirm the starting point: the review suite is
      green at 291 tests, and `plugins/s/skills/review/references/verification.md`'s
      "What the verifier receives" names the candidate index, location, claim
      and why, and no rubric.
- [x] 1.2 [req: review-skill] In that same section, require the spawn message
      to carry the severity rubric, quoted verbatim from the rating step the
      composing session has just read — the `high`, `medium` and `low`
      definitions, the impact rule with its concrete instances, and the
      exposure floor. State that it is quoted rather than reproduced here, and
      why: the rubric has changed in four of the last ten versions, and a
      second copy in this file would be a second source to drift.
- [x] 1.3 [req: review-skill] State in the same place why the whole rubric
      travels rather than only the concrete instances: the exposure floor is
      the rubric's one absolute, a verifier that downgraded a credential
      exposure or an authorization-boundary finding would be a worse failure
      than a low-versus-medium drift, and no benchmark severity target is an
      exposure case, so that failure would go unmeasured.
- [x] 1.4 [req: review-skill] Do not add a copy of the rubric's text to
      `plugins/s/skills/review/references/verification.md`. If you find yourself pasting the `high`,
      `medium` and `low` definitions into that file, stop — the instruction is
      to quote at runtime, and a checked-in copy is the defect this task
      exists to avoid.

## 2. The harness body

- [x] 2.1 [req: review-skill] Apply the same requirement in
      `plugins/s/harness/bodies/review.md`'s verify step, pointing at that
      body's own rubric step rather than at `SKILL.md`, since a
      harness-installed review has no `SKILL.md` to quote from. Keep the
      substance inline. The worst-case rendered body is 189 of 200, so there is
      room; report the number afterwards.

## 3. Tests

- [x] 3.1 [req: review-skill] Add a test to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning that
      both surfaces require the severity rubric to travel in the spawn message.
      Guard patterns against markdown emphasis with a class such as `[*_\s]+`.
- [x] 3.2 [req: review-skill] Add a test that
      `plugins/s/skills/review/references/verification.md` does **not** contain its own copy of the
      rubric's severity definitions — assert the absence of the `high` and
      `medium` definition wording that lives in the rating step. Prove both
      tests fail against the pre-change text before trusting them.

## 4. Version and verification

- [x] 4.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.270` to `0.6.271`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      291-test baseline.
- [x] 4.3 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs271.log 2>&1;
      tail -4 /tmp/bs271.log` — and report the verdict verbatim.
- [x] 4.4 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 4.5 [req: *] Report the worst-case rendered harness body across every
      registered harness against the 200 ceiling, and `SKILL.md`'s line count
      against 400. Measure both at the end of your work, not partway through —
      a count taken mid-build staled by three lines on the last change.
- [x] 4.6 [req: review-skill] Read the finished spawn-message description on
      both surfaces as a stranger composing the spawn, and answer one question:
      would you know, without inferring, that the severity rubric must be in
      the message, and where to get its text? Quote what you read. If the
      answer is no, that is the defect this change exists to remove.
