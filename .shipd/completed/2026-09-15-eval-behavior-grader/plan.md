# eval-behavior-grader
Status: verified

## Idea

Add a behavior-based eval grader and a `/s:fix` eval case, so a run can assert
that the produced software works rather than that the produced artifacts are
well-formed.

### Motivation

`evals/run.py`'s `grade()` asserts structure only — one change directory,
`spec_lint.py` exit 0, `Status: ready` — so the harness grades shipd's artifacts
with shipd's own linter, and no eval covers `/s:fix` or `/s:build` at all.

### Details

- Add a per-case `expect.json` that selects the grader; when absent the case
  grades structurally, so the three existing `/s:plan` cases are untouched.
- Add a behavior grader: restore the case's shipped tests, copy its held-out
  `verify/` tree into the scratch repo after the session, run the fixture's
  suite, and pass only on exit 0.
- Add the `fix-report-drift` case: a fixture carrying a `verified/` capability,
  a seeded drift bug, a green suite, and a held-out test kept outside
  `fixture/`.
- Convert `evals/tests/test_runner.py` from pytest to stdlib `unittest` and add
  a `unittest discover -s evals/tests` step to `.github/workflows/ci.yml`.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`,
`evals/tests/test_runner.py`, `.github/workflows/ci.yml`, and a new
`evals/cases/fix-report-drift/` tree. No new dependencies — stdlib only.
Nothing under `plugins/s/` changes, so no plugin version bump.

### Non-goals

- No no-skill baseline arm and no A/B comparison; that is a follow-up change
  built on this grader.
- No `/s:build` or `/s:epic` eval case — this change adds `/s:fix` only.
- No LLM-as-judge grading; the held-out test is the only behavioral oracle.
- No assertion that the session wrote its own regression test.
- No change to the structural assertions the three existing cases grade under.

## Implementation

- **A per-case `evals/cases/<name>/expect.json` selects the grader**, with
  `{"grader": "behavior"}` the only non-default value and an absent file
  meaning `structural`. The `skill-evals` capability rejected `expect.json` at
  v1 as premature because both cases shared one contract; two graders now exist,
  so that premise is gone. Rejected: inferring the grader from fixture shape
  (implicit, and wrong for a fix case with no `tests/`), and case-name prefixes
  (couples naming to behavior).
- **The oracle is held out of the fixture.** The failing test lives at
  `evals/cases/<name>/verify/`, outside `fixture/`, and is copied into the
  scratch repo only after the session ends. Rejected: shipping it inside
  `fixture/` — a test the session can read is not a hidden oracle, and the
  session could edit it until it passes.
- **Grade the whole suite, not a named test.** After copying, the grader runs
  `python3 -m unittest discover -s tests` in the scratch root and passes only on
  exit 0. One assertion subsumes both "the held-out test passes" and "nothing
  previously green broke", and no test-id parsing is needed. Rejected: naming
  test ids in `expect.json`.
- **Restore the case's shipped `tests/` before copying `verify/`.** A session
  that weakened or deleted a shipped test would otherwise game the grade; the
  restore reverts edits to shipped tests while leaving any new file the session
  added in place, which is graded on nothing per the decision below.
- **The grader asserts the fix only.** No assertion that the session added its
  own regression test, so the same oracle can grade a future no-skill baseline
  arm unchanged. Rejected: also asserting a new test appeared — it bakes a
  `/s:fix`-specific mandate into a grader the A/B needs to stay arm-neutral.
- **`assemble_scratch` sanity-checks a behavior fixture**: the shipped suite
  must exit 0 before the session, and must exit non-zero once `verify/` is
  copied in. A mis-seeded fixture — bug absent, or held-out test already
  passing — otherwise passes every run silently and reports a false green.
- **The fixture drifts from a documented contract, not from silence.** Its
  `.shipd/verified/report-output/` capability documents rows sorted by team then
  name; `src/report.py` iterates `ROWS` in declaration order. This lands
  `/s:fix` unambiguously in its branch A (code drifted from documented
  behavior) rather than branch B (hand off to `/s:plan`).
- **New tests are stdlib `unittest`, and CI discovers them.** `test_runner.py`'s
  `tmp_path` usages become `tempfile.TemporaryDirectory` in `setUp`, and
  `ci.yml` gains a discover step. `evals/tests/` runs nowhere today and pytest
  is not installed, so adding pytest tests there would add more dead weight.

Risk: the grader executes fixture test code in the scratch directory. That is
already true of the bypass-permissions session that precedes it; the scratch cwd
and the dev-only scope bound it, and `--keep-scratch` remains the inspection
path.

## Questions and answers

### Q1: Which test framework do the new grader tests use, and does CI run them?
- **Question:** The new grader needs tests, but `evals/tests/test_runner.py` is
  pytest-style, pytest is not installed, and `evals/tests/` is absent from
  `ci.yml` while six other suites run under `unittest discover`. Options:
  (a) convert the existing file to `unittest` and wire `evals/tests` into CI;
  (b) add pytest tests to the existing file; (c) a new `unittest` file with no
  conversion and no CI. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — convert `test_runner.py` to stdlib `unittest` and add
  a `unittest discover -s evals/tests` step to `ci.yml`. It matches the pattern
  the `semantic-review`, `shipd-document`, and `shipd-port` capabilities already
  require of a new suite, and it stops the harness from accumulating tests that
  never execute.
- **Queued:** q-evals-tests-framework-and-ci-wiring

### Q2: Does the behavior grader assert the regression test, or only the fix?
- **Question:** `/s:fix` mandates a regression test alongside a code fix. Should
  the grader assert only that the held-out test flips to passing with the
  shipped suite still green, or additionally that the session added a test?
  Options: (a) grade the fix only; (b) grade the fix and the added test.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — grade the fix only. An eval grader asserts the
  outcome under test, never a discipline specific to the skill being graded, so
  a future no-skill baseline arm can be graded by exactly the same oracle.
- **Queued:** q-eval-fix-grader-scope
