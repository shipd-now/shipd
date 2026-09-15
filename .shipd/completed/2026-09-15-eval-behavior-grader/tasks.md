## 1. Convert the eval tests to unittest and wire CI

- [x] 1.1 [req: evals-ci-discovery] In `evals/tests/test_runner.py`, replace the
      pytest `tmp_path` fixture with stdlib `unittest`: group the existing test
      functions into `unittest.TestCase` classes, create a per-test directory
      with `tempfile.TemporaryDirectory` in `setUp`, drop the `import pytest`,
      and replace the `pytest.main` block at the file's end with
      `unittest.main()`. Keep every existing assertion's meaning unchanged.
- [x] 1.2 [req: evals-ci-discovery] Run
      `python3 -m unittest discover -s evals/tests -v` and confirm every
      converted test passes with no third-party package installed.
- [x] 1.3 [req: evals-ci-discovery] In `.github/workflows/ci.yml`, add a step
      named `Run eval harness test suite` running
      `python3 -m unittest discover -s evals/tests -v`, placed directly after
      the existing `Run engine test suite` step.

## 2. Per-case grader selection

- [x] 2.1 [req: case-grader-selection] In `evals/tests/test_runner.py`, add
      tests for a new `read_expect(case_dir)` helper: an absent `expect.json`
      yields grader `structural`, a file without a `grader` key yields
      `structural`, `{"grader": "behavior"}` yields `behavior`, and an
      unrecognized value or unreadable JSON raises. Run them and observe them
      fail — the helper does not exist yet.
- [x] 2.2 [req: case-grader-selection] In `evals/run.py`, add `read_expect` and
      a `grader` field on the `Case` dataclass, populated during
      `discover_cases` from the case directory's `expect.json`.
- [x] 2.3 [req: case-grader-selection] In `evals/run.py`'s `execute_case`,
      dispatch on `case.grader`: `structural` calls the existing `grade`,
      `behavior` calls the new `grade_behavior` added in task 3.2. An
      unrecognized grader or unreadable `expect.json` records the run as failed
      with a message naming the case and the offending value. Confirm the
      task 2.1 tests now pass.

## 3. The behavior grader

- [x] 3.1 [req: behavior-grading] In `evals/tests/test_runner.py`, add tests for
      `grade_behavior(case, scratch_dir)` against prebaked scratch trees: a
      passing suite grades passed; a failing held-out test grades failed; a
      broken shipped test grades failed; and a scratch tree whose shipped test
      was emptied still grades failed because the restore reverted it. Run them
      and observe them fail.
- [x] 3.2 [req: behavior-grading] In `evals/run.py`, add `grade_behavior(case,
      scratch_dir)`: copy `<case>/fixture/tests/` over `<scratch>/tests/`, then
      copy `<case>/verify/` over `<scratch>/tests/`, then run
      `[sys.executable, "-m", "unittest", "discover", "-s", "tests"]` with
      `cwd=scratch_dir`, returning `RunResult(True)` on exit 0 and
      `RunResult(False, <captured output>)` otherwise. Confirm the task 3.1
      tests now pass.

## 4. Fixture sanity check

- [x] 4.1 [req: behavior-fixture-sanity] In `evals/tests/test_runner.py`, add
      tests for a new `check_behavior_fixture(case, scratch_dir)`: it returns no
      failure for a correctly seeded fixture, a failure naming the shipped-suite
      check when the fixture's own suite is red, and a failure naming the
      held-out check when the held-out test already passes. Run them and observe
      them fail.
- [x] 4.2 [req: behavior-fixture-sanity] In `evals/run.py`, add
      `check_behavior_fixture` implementing those two probes on a throwaway copy
      of the scratch tree, and call it from `execute_case` for a behavior case
      immediately after `assemble_scratch` — recording the run as failed and
      returning before `run_conversation` is invoked when it reports a failure.
      Confirm the task 4.1 tests now pass.

## 5. The fix-report-drift case

- [x] 5.1 [req: behavior-grading] Create the spec tree under
      `evals/cases/fix-report-drift/fixture` — a content directory holding
      verified/report-output/spec.md, whose `report-row-order` requirement
      states the `report` command SHALL print its rows sorted by team ascending
      then name ascending, with a `#### Scenario:` covering that order. Mirror
      the empty-directory .gitkeep entries the existing fixtures carry, listed
      by `find evals/cases/plan-csv-export -type f`.
- [x] 5.2 [req: behavior-grading] Copy
      `evals/cases/plan-csv-export/fixture/src/report.py` to the same relative
      location under `evals/cases/fix-report-drift/fixture`, unchanged: its
      `main()` iterates `ROWS` in declaration order and so drifts from the sort
      order task 5.1 documented.
- [x] 5.3 [req: behavior-grading] Add a tests/test_report.py under
      `evals/cases/fix-report-drift/fixture`, a stdlib `unittest` suite
      asserting the header line and the column padding of `report.main()`'s
      output — behavior the fixture already satisfies, so the shipped suite is
      green. Reach the module by inserting the fixture's src directory onto
      `sys.path` relative to the test file, the same way
      `evals/tests/test_runner.py:20` reaches `run.py`.
- [x] 5.4 [req: behavior-grading] Add a test_report_order.py under
      `evals/cases/fix-report-drift/verify`, a stdlib `unittest` test asserting
      `report.main()` prints carol, then alice, then bob — the documented order
      the seeded code violates. Use the same `sys.path` insertion as task 5.3,
      so the file runs correctly once copied into the scratch repo's tests
      directory.
- [x] 5.5 [req: case-grader-selection] Create
      `evals/cases/fix-report-drift/expect.json` containing
      `{"grader": "behavior"}`, and `evals/cases/fix-report-drift/prompt.md`
      invoking `/s:fix` on the symptom — that `report` prints rows in the wrong
      order — without naming the sorting rule or the file to edit.
- [x] 5.6 [req: behavior-fixture-sanity] Run
      `python3 evals/run.py --case fix-report-drift --keep-scratch` and confirm
      the run reaches a graded verdict, then inspect the kept scratch directory
      to confirm the sanity check passed and the held-out test was the failing
      one before the session.

## 6. Document the harness

- [x] 6.1 [req: case-grader-selection] `AGENTS.md` carries no eval guidance
      today (its only `##` sections are the plugin-cache note, Workflow, and
      Workflow's two subsections). Add a new `## Evals` section after
      `## Workflow` covering how to run `evals/run.py`, the two grader modes,
      the `expect.json` key, and the held-out `verify/` convention, naming
      `evals/cases/fix-report-drift` as the worked example.

## 7. Grader-aware conversation driving

- [x] 7.1 [req: grader-aware-driving] In `evals/tests/test_runner.py`, add tests
      for the grader-aware resume loop: a behavior case's gate returns the
      behavior verdict rather than the structural one, the reply sent to a
      behavior case carries no emission/lint/promotion instruction, and probing
      the gate leaves the scratch tree free of any file from the case's
      held-out tree. Run them and observe them fail.
- [x] 7.2 [req: grader-aware-driving] In `evals/run.py`, add a skill-neutral
      resume reply constant beside `GOAHEAD_REPLY` that asks the session to
      proceed and take its own recommended option, with no mention of emitting,
      linting, or promoting a change.
- [x] 7.3 [req: grader-aware-driving] In `evals/run.py`, give
      `run_conversation` access to the case's grader and select both the gate
      and the reply from it: a structural case keeps today's `grade` gate and
      `GOAHEAD_REPLY`; a behavior case gates on `grade_behavior` evaluated
      against a throwaway copy of the scratch directory — never the scratch
      directory itself — and sends the task 7.2 reply. Confirm the task 7.1
      tests now pass.
- [x] 7.4 [req: grader-aware-driving] Run
      `python3 -m unittest discover -s evals/tests` and confirm the whole
      converted suite still passes.
- [x] 7.5 [req: grader-aware-driving] Re-run
      `python3 evals/run.py --case fix-report-drift --keep-scratch`, capturing
      its stdout to a file so the printed verdict survives the shell. Confirm
      the summary reports the case at 1/1 and that the kept scratch directory
      holds exactly one `eval-transcript.json` with no `-turn2` sibling —
      evidence the grader-aware gate stops the loop once the fix lands instead
      of spending the resume cap.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 154 | 64.0k |
| Edit | 19 | 36.1k |
| Read | 40 | 22.2k |
| Write | 6 | 10.7k |
| (no tool) | 0 | 5.2k |
| ToolSearch | 3 | 2.4k |
| Agent | 3 | 1.9k |
| Monitor | 1 | 310 |
| TaskStop | 1 | 58 |
| **Total** | 227 | 142.8k |
