## 1. The gate fails loudly when nothing was reviewed

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, rename
      `test_a_nonzero_cli_run_leaves_pending`,
      `test_a_timed_out_cli_run_leaves_pending` and
      `test_a_timed_out_poll_leaves_pending` to `..._fails_loudly` and pass
      `expect_failure=True` to their `cli_gate`/`gate` calls. Keep every
      existing assertion — the status must still be the single `pending` post,
      and no review may be published. The harness already supports the flag at
      line 1702; add nothing to it. Run
      `python3 -m unittest plugins.s.skills.build.tests.test_copilot_verb` and
      observe exactly those three fail.
- [x] 1.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, change the CLI
      branch's `exit 0` (the `if [[ ! -f "$body_file" ]]` case, line 450) to
      `exit 1`, redirect its message to stderr, and extend the message to name
      the reviewer step's log as where the cause is reported and that an
      exhausted Copilot quota appears there as "exceeded your monthly quota".
      Leave the `pending` status untouched — nothing was judged.
- [x] 1.3 [req: gate-workflow-template] In the same file, change the poll
      branch's timeout `exit 0` (line 489) to `exit 1` and redirect its message
      to stderr. Leave the moved-head `exit 0` at line 471 exactly as it is,
      and add a comment there saying it stays zero because that run handed the
      gate to the newer push rather than stalling.
- [x] 1.4 [req: gate-workflow-template] Update the "Timeout semantics"
      paragraph in the same file's header comment so it states that these two
      paths leave the status pending **and fail the job**, and why exiting zero
      was wrong. Confirm 1.1 now passes.

## 2. Low findings are reported but never anchored

- [x] 2.1 [req: gate-workflow-template] Add tests to
      `plugins/s/skills/build/tests/test_copilot_verb.py` covering the anchor
      loop's severity gate: a `high` finding whose path and range are in the
      diff is anchored; a `medium` one is anchored; a `low` one whose path and
      range are equally present is **not** anchored and instead appears in the
      body's "Findings not anchored to the diff" block. Follow the existing
      `GateCliReviewerTest` conventions for driving the step. Run the suite and
      observe the low-severity case fail.
- [x] 2.2 [req: gate-workflow-template] In the embedded Python of
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, in the anchor
      loop at line 779, route a finding whose `severity(finding)` is not
      `high` or `medium` to `unverified` before the `placed()` call, so it
      renders through the existing `prose()` block. Add a comment stating that
      an inline comment opens a review thread and a repository requiring
      conversation resolution would otherwise let a `low` finding block a merge
      the rubric says it never blocks. Confirm 2.1 passes.

## 3. The required check accepts any reporting source

- [x] 3.1 [req: required-check-protect] Add tests to
      `plugins/s/skills/review/tests/test_review_gate.py` asserting that the
      body `_protection_put_body` builds carries a `checks` list whose
      `semantic-review` entry has an `app_id` of `None`, carries no `contexts`
      key, and still preserves `strict` and the other protection fields.
      Cover the unprotected-branch creation path too. Run
      `python3 -m unittest plugins.s.skills.review.tests.test_review_gate` and
      observe them fail.
- [x] 3.2 [req: required-check-protect] In
      `plugins/s/skills/review/scripts/review_gate.py`, change
      `_protection_put_body` (line 608) to emit
      `"checks": [{"context": c, "app_id": None} for c in contexts]` in place
      of `"contexts": list(contexts)`, keeping `strict` and every other
      preserved field as they are. Add a docstring line stating that a null
      `app_id` means any source may report the check, which is what lets a
      status posted by a person satisfy the requirement. Confirm 3.1 passes.
- [x] 3.3 [req: required-check-protect] Add one idempotence regression test to
      `plugins/s/skills/review/tests/test_review_gate.py`: a protection GET
      whose `required_status_checks` carries **both** a `contexts` list and a
      `checks` list (the shape GitHub returns, confirmed against a live
      protected branch) with `semantic-review` already present and conversation
      resolution on. Assert `protect` reports it already required, performs no
      write, and exits zero. The reader at line 645 takes `contexts`, which the
      GET still returns after this change writes `checks` — this test pins that
      so a later reader change cannot silently break idempotence. Make no
      change to `protect`'s reader.

## 4. Verification

- [x] 4.1 [req: *] Run both suites —
      `python3 -m unittest plugins.s.skills.build.tests.test_copilot_verb` and
      `python3 -m unittest plugins.s.skills.review.tests.test_review_gate` —
      and confirm both report OK with no failures. The clean-worktree baselines
      were 150 and 68 tests respectively, so the totals must be at least those.
- [x] 4.2 [req: *] Confirm the workflow template still parses: load
      `plugins/s/integrations/copilot/copilot-review-gate.yml` as YAML, run
      `bash -n` over every step's `run` script, and compile the embedded Python
      of the posting step. All three must succeed.
- [x] 4.3 [req: *] Confirm no third-party import entered the engine: the
      constitution requires `plugins/s/skills/review/scripts/review_gate.py` to
      stay importable with only the Python 3 standard library.
