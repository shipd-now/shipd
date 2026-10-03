## 1. The `change` member on both payload surfaces

- [x] 1.1 [req: fast-pass-eligibility] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add a failing
      test asserting that `plugins/s/skills/review/references/json-output.md`
      and `plugins/s/harness/references/review.md` both document a `change`
      member carrying `slug`, `location`, and `dir`. Run it and observe it
      fail — neither surface names the member yet.
- [x] 1.2 [req: fast-pass-eligibility] In
      `plugins/s/skills/review/references/json-output.md`, add the `change`
      member to the shape block as
      `"change": { "slug": "…", "location": "planned" | "completed", "dir": "…" }`
      and state in the rules paragraph that it is present only when a change is
      in scope, exactly as `spec_coverage` is.
- [x] 1.3 [req: fast-pass-eligibility] In
      `plugins/s/harness/references/review.md`, add the identical `change`
      member and the same presence sentence beside its existing
      `spec_coverage` line, then confirm `test_skill_references.py` passes.
- [x] 1.4 [req: fast-pass-eligibility] In
      `plugins/s/skills/review/SKILL.md` and
      `plugins/s/skills/review/references/spec-aware.md`, instruct the skill to
      carry the `change`, `location`, and `dir` values that
      `semdiff change` already reports into the `--json` object's `change`
      member whenever spec-aware mode resolved a change.

## 2. Poster eligibility and arming

- [x] 2.1 [req: fast-pass-eligibility] In
      `plugins/s/skills/review/tests/test_review_gate.py`, add failing unit
      tests for a `fast_pass_eligible` predicate covering: an eligible review
      (completed location, `pass` verdict, every `spec_coverage` state `met`,
      variable `true`); one `cant-tell` state; one `unmet` state; a `planned`
      location; an empty `spec_coverage`; an absent `change` member; a
      `changes-requested` verdict under the `none` disposition; and a variable
      read exiting non-zero. Run them and observe them fail.
- [x] 2.2 [req: fast-pass-eligibility] In
      `plugins/s/skills/review/scripts/review_gate.py`, add the
      `fast_pass_eligible` predicate implementing those cases, reading the
      review object's `verdict`, `change.location`, and `spec_coverage` and
      never calling `status_state`. Confirm the 2.1 tests pass.
- [x] 2.3 [req: fast-pass-eligibility] In `test_review_gate.py`, add failing
      tests over `post` through the injectable `gh` runner asserting: an
      eligible review runs `variable get SHIPD_FAST_PASS` and then
      `pr merge --auto --squash --delete-branch` after the status call; an
      ineligible one runs no merge call and the summary comment names the unmet
      condition; and a merge call exiting non-zero leaves the posted status and
      the command's own exit unchanged.
- [x] 2.4 [req: fast-pass-eligibility] In `review_gate.py`'s `post` path,
      implement the variable read, the arming call ordered after the status
      write, the summary-comment line recording whether the fast-pass armed or
      which condition was unmet, and the non-fatal handling of an arming
      failure. Confirm the 2.3 tests pass.

## 3. The copilot templates

- [x] 3.1 [req: fast-pass-workflow-arming] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add a failing test
      asserting `plugins/s/integrations/copilot/SKILL.md` names
      `<!-- shipd-fast-pass: eligible -->`, places it directly above the
      verdict marker, and still states the verdict marker is the body's last
      line. Run it and observe it fail.
- [x] 3.2 [req: fast-pass-workflow-arming] In
      `plugins/s/integrations/copilot/SKILL.md`, add the fast-pass line
      instruction: emit it directly above the verdict marker, and only where
      the pull request carries a completed shipd change directory whose every
      delta scenario the agent judged met. Confirm the 3.1 test passes.
- [x] 3.3 [req: fast-pass-workflow-arming] In `test_copilot_verb.py`, add a
      failing test asserting
      `plugins/s/integrations/copilot/copilot-review-gate.yml` reads
      `vars.SHIPD_FAST_PASS` in a step environment, scans the body for the
      fast-pass line by whole-line equality bounded to 200 lines, arms
      `gh pr merge --auto --squash --delete-branch` only when the matched
      verdict state came from a `ship-it` marker, and does not fail the job
      when the arming call fails.
- [x] 3.4 [req: fast-pass-workflow-arming] In `copilot-review-gate.yml`, add
      the fast-pass scan and the arming call to the classify step after the
      `post_status` call, gated on the variable, on `matched_state` being
      `success`, and on the fast-pass line being found; log the unmet condition
      otherwise. Confirm the 3.3 test passes.

## 4. The doctor check

- [x] 4.1 [req: doctor-github-checks] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add failing tests for a
      `check_fast_pass` function behind the injectable runner covering a
      variable reading `true`, an absent variable, a value other than `true`,
      and a denied read — each expecting an `ok` line and never a `warn` — plus
      a test asserting the GitHub-side checks report in the order
      `protection`, `automerge`, `copilot-secret`, `fast-pass`.
- [x] 4.2 [req: doctor-github-checks] In `plugins/s/bin/shipd`, add
      `check_fast_pass` beside `check_copilot_secret`, reading
      `SHIPD_FAST_PASS` read-only through the same runner and honoring the
      existing `context["skip"]` short-circuit, then append it to the check
      list after `check_copilot_secret`. Confirm the 4.1 tests pass.
- [x] 4.3 [req: doctor-fast-pass-line] In `plugins/s/skills/doctor/SKILL.md`,
      add `fast-pass` to the parsed check-name list and state it is
      report-only with no remedy row; mirror that statement in
      `plugins/s/harness/references/doctor.md`, whose opening sentence names
      the remediable checks.

## 5. The gate consent row

- [x] 5.1 [req: gate-fast-pass-consent] In
      `plugins/s/skills/gate/SKILL.md`, add the fast-pass row to the step-5
      consent table running `gh variable set SHIPD_FAST_PASS --body true`,
      stating what it permits, omitted alongside the auto-merge option under
      `pr-mode: draft`, and add `fast-pass` to the closing `shipd doctor`
      lines the skill relays; state in the update flow that it sets no
      variable.
- [x] 5.2 [req: gate-fast-pass-consent] In
      `plugins/s/harness/bodies/gate.md`, mirror the fast-pass consent step and
      the four relayed doctor lines, so the harness body states the same flow
      as the skill.

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, `python3
      plugins/s/skills/build/scripts/spec_lint.py`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py fast-pass-auto-merge`, and
      confirm every suite and both lints pass.
