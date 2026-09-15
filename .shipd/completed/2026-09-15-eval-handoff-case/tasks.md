## 1. Recognize the handoff grader

- [x] 1.1 [req: case-grader-selection] In `evals/tests/test_runner.py`, add
      tests for `read_expect`: `{"grader": "handoff", "handoff_requirement":
      "x"}` yields the handoff grader and that requirement id; `{"grader":
      "handoff"}` with no `handoff_requirement` raises ValueError naming the
      case and the missing key; the existing structural and behavior cases are
      unaffected. Run them and observe them fail.
- [x] 1.2 [req: case-grader-selection] In `evals/run.py`, add `"handoff"` to
      `RECOGNIZED_GRADERS`, give `Case` a `handoff_requirement` field defaulting
      to `None`, and have `read_expect` return both the grader and that id,
      raising when a handoff case omits it. Populate the field in
      `discover_cases`. Confirm the task 1.1 tests pass.

## 2. The handoff grader

- [x] 2.1 [req: handoff-grading] In `evals/tests/test_runner.py`, add tests for
      `grade_handoff(case, scratch_dir)` against prebaked scratch trees: an
      untouched tree whose transcript names the requirement id passes; a tree
      with an edited `src/` file fails naming that path; a tree with an edited
      content-directory file fails naming that path; an untouched tree whose
      transcript omits the id fails naming the id; and an untouched tree whose
      transcript names the id but never mentions `/s:plan` still passes. Run
      them and observe them fail.
- [x] 2.2 [req: handoff-grading] In `evals/run.py`, add a `_tree_differs(a, b)`
      helper returning the first relative path whose content differs between two
      directories, or `None` when they match, skipping `__pycache__`.
- [x] 2.3 [req: handoff-grading] In `evals/run.py`, add
      `grade_handoff(case, scratch_dir)` asserting, in order: `src/` matches the
      fixture's, the scratch content directory matches the fixture's, the
      shipped suite exits 0, and the session's final `result` text from the
      scratch transcript contains `case.handoff_requirement`. Read the transcript
      via a helper that prefers the highest-numbered `eval-transcript-turn<N>.json`
      and falls back to `eval-transcript.json`. Return a failure naming which
      assertion failed. Confirm the task 2.1 tests pass.
- [x] 2.4 [req: handoff-grading] In `evals/run.py`'s `execute_case`, dispatch
      `case.grader == "handoff"` to `grade_handoff`, leaving the structural and
      behavior paths unchanged.

## 3. Sanity check and arm acceptance

- [x] 3.1 [req: handoff-fixture-sanity] In `evals/tests/test_runner.py`, add
      tests for `check_handoff_fixture(case, scratch_dir)`: it returns `None`
      for a fixture whose shipped suite passes, and a message naming the check
      for one whose suite fails. Add a test that `execute_case` records the run
      as failed and spawns no session when it reports a failure. Run them and
      observe them fail.
- [x] 3.2 [req: handoff-fixture-sanity] In `evals/run.py`, add
      `check_handoff_fixture` running the shipped suite on a throwaway copy of
      the scratch tree and requiring exit 0, and call it from `execute_case`
      immediately after `assemble_scratch` for a handoff case. Confirm the task
      3.1 tests pass.
- [x] 3.3 [req: handoff-accepts-arms] In `evals/tests/test_runner.py`, add a
      test that `_arm_refusal` returns `None` for a handoff case under the
      `baseline` arm, so both arms run. Confirm it passes without changing
      `_arm_refusal`; if it does not pass, fix `_arm_refusal` to refuse only a
      structural grader.

## 4. The fix-spec-wrong case

- [x] 4.1 [req: handoff-grading] Create the spec tree under
      `evals/cases/fix-spec-wrong/fixture` — a content directory holding
      verified/report-output/spec.md, whose `report-column-width` requirement
      states the `report` CLI SHALL print the name column left-justified to a
      fixed width of six characters, with a `#### Scenario:` covering it. Mirror
      the empty-directory .gitkeep entries listed by
      `find evals/cases/fix-report-drift -type f`.
- [x] 4.2 [req: handoff-grading] Add a src/report.py under
      `evals/cases/fix-spec-wrong/fixture` that faithfully implements that
      contract with the format `"%-6s  %3d  %s"`, and whose `ROWS` include one
      name longer than six characters so the table visibly misaligns for that
      row while the code still matches its documented width.
- [x] 4.3 [req: handoff-grading] Add a tests/test_report.py under
      `evals/cases/fix-spec-wrong/fixture`, a stdlib `unittest` suite asserting
      the header line and the six-character padding for the rows whose names fit
      — behavior the code satisfies, so the shipped suite is green. Reach the
      module by inserting the fixture's src directory onto `sys.path` the way
      `evals/cases/fix-report-drift/fixture/tests/test_report.py` does. Add no
      assertion covering the long-name row.
- [x] 4.4 [req: case-grader-selection] Create
      `evals/cases/fix-spec-wrong/expect.json` containing
      `{"grader": "handoff", "handoff_requirement": "report-column-width"}`, and
      `evals/cases/fix-spec-wrong/prompt.md` invoking `/s:fix` on the symptom —
      the table's columns do not line up for longer names — without naming the
      requirement, the width rule, or the file to edit.

## 5. Verify and document

- [x] 5.1 [req: handoff-grading] Run `python3 -m unittest discover -s
      evals/tests` and confirm the whole suite passes with no third-party
      package installed.
- [x] 5.2 [req: handoff-fixture-sanity] Without spawning a session, confirm the
      fixture is correctly seeded: run the shipped suite directly against
      `evals/cases/fix-spec-wrong/fixture` and observe it exit 0, and run its
      `report.py` and observe the long-name row misaligning against the header.
- [x] 5.3 [req: case-grader-selection] In `AGENTS.md`'s `## Evals` section,
      document the `handoff` grader, its `handoff_requirement` key, its four
      assertions, why the positive signal is a requirement id rather than a
      skill name, and name `evals/cases/fix-spec-wrong` as the worked example.

## 6. Grade against the pre-session snapshot

- [x] 6.1 [req: handoff-grading] In `evals/tests/test_runner.py`, replace
      `_untouched_handoff_scratch`'s raw `shutil.copytree` with the runner's own
      `assemble_scratch`, so every handoff grader test exercises the real
      assembly path. Run the suite and observe the handoff tests fail: assembly
      injects a content-directory file the fixture does not ship.
- [x] 6.2 [req: handoff-grading] In `evals/run.py`, snapshot the scratch `src/`
      tree and content directory immediately after `assemble_scratch` and before
      `run_conversation`, and have `grade_handoff` compare the post-session tree
      against that snapshot rather than against `case.fixture_path`. Carry the
      snapshot to the grader by whatever means keeps `grade_handoff`'s signature
      testable. Confirm the task 6.1 tests now pass.
- [x] 6.3 [req: handoff-grading] Add a test asserting the failure message names
      the actually-edited path: edit only `.shipd/verified/report-output/spec.md`
      in an assembled scratch and assert the reported path is that spec, not any
      other content-directory file. Add the mirror test for a missing
      requirement id, asserting the failure names the id rather than a path.
- [x] 6.4 [req: handoff-grading] Run `python3 -m unittest discover -s
      evals/tests` and confirm the whole suite passes.
