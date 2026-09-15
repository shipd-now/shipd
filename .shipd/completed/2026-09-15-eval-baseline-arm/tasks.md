## 1. Derive the baseline prompt

- [x] 1.1 [req: derived-baseline-prompt] In `evals/tests/test_runner.py`, add
      tests for a new `baseline_prompt(text)` helper in `evals/run.py`: a first
      line opening `/s:fix ` yields that line without the token plus the
      remaining lines verbatim; a `/s:plan` token is stripped the same way;
      text whose first line carries no `/s:` token raises ValueError naming the
      problem. Run them and observe them fail — the helper does not exist yet.
- [x] 1.2 [req: derived-baseline-prompt] In `evals/run.py`, add
      `baseline_prompt(text)` implementing exactly that, raising ValueError for
      a first line with no leading `/s:<skill>` token. Confirm the task 1.1
      tests now pass.

## 2. Thread the arm through the session invocation

- [x] 2.1 [req: arm-selection] In `evals/tests/test_runner.py`, add tests
      asserting `_run_turn` builds its command with `--plugin-dir` under the
      treatment arm and without it under the baseline arm, with the working
      directory, `--permission-mode`, and `--output-format` identical in both.
      Capture the command via the injectable runner seam or by monkeypatching
      `subprocess.run`. Run them and observe them fail.
- [x] 2.2 [req: arm-selection] In `evals/run.py`, give `_run_turn` an `arm`
      parameter defaulting to `"treatment"` and omit the `--plugin-dir` pair
      from `cmd` when it is `"baseline"`. Change nothing else about the command.
- [x] 2.3 [req: arm-selection] In `evals/run.py`, thread `arm` from
      `run_conversation` into the bound runner it passes to
      `session_driver.drive`, and send `baseline_prompt(...)` of the case's
      prompt as turn 1 under the baseline arm, the raw prompt under treatment.
      Confirm the task 2.1 tests now pass.

## 3. Refuse the arms that cannot inform

- [x] 3.1 [req: baseline-requires-behavior] In `evals/tests/test_runner.py`,
      add tests that a structural case run under `--arm baseline` and under
      `--arm both` is recorded as failed with a message naming the case and its
      grader, that no session is spawned (spy on `run_conversation`), and that
      a behavior case under the same arms proceeds. Run them and observe them
      fail.
- [x] 3.2 [req: derived-baseline-prompt] In `evals/tests/test_runner.py`, add a
      test that a behavior case whose `prompt.md` opens with no `/s:` token is
      recorded as failed naming the case, with no session spawned, when run
      under the baseline arm. Run it and observe it fail.
- [x] 3.3 [req: baseline-requires-behavior] In `evals/run.py`'s `execute_case`,
      add an `arm` parameter and refuse both cases before `assemble_scratch`:
      a structural grader under a baseline-bearing arm, and a `prompt.md` whose
      `baseline_prompt` raises. Each records every requested run as failed with
      the naming message and spawns no session. Confirm tasks 3.1 and 3.2 pass.

## 4. Per-arm reporting and exit code

- [x] 4.1 [req: pass-rate-reporting] In `evals/tests/test_runner.py`, add tests
      for `summarize` carrying per-arm results: a single-arm mapping renders
      exactly as it does today; a two-arm mapping renders one labelled row per
      arm per case; an all-pass treatment with an all-fail baseline returns exit
      code 0; and a failing treatment returns 1 whatever the baseline did. Run
      them and observe them fail.
- [x] 4.2 [req: pass-rate-reporting] In `evals/run.py`, key the results
      structure `summarize` consumes by `(case, arm)` rather than case alone,
      render a labelled row per arm, and compute the exit code from treatment
      rows only. Keep the single-arm rendering byte-identical to today's so the
      default invocation is unchanged. Confirm the task 4.1 tests pass.
- [x] 4.3 [req: arm-selection] In `evals/run.py`, add the `--arm` argument to
      `build_arg_parser` with choices `treatment`, `baseline`, `both` and
      default `treatment`, and have `main` execute each selected arm per case,
      passing `arm` into `execute_case`.

## 5. Verify and document

- [x] 5.1 [req: arm-selection] Run `python3 -m unittest discover -s evals/tests`
      and confirm the whole suite passes with no third-party package installed.
- [x] 5.2 [req: arm-selection] Run `python3 evals/run.py --case plan-csv-export
      --arm baseline` and confirm it refuses immediately, naming the case and
      its structural grader, without spawning a session. This costs no model
      spend because the refusal precedes the session.
- [x] 5.3 [req: arm-selection] In `AGENTS.md`'s `## Evals` section, document
      `--arm`, the derived baseline prompt and why parity is structural rather
      than authored, the two refusals, and the treatment-only exit code.

## 6. A refused run exits non-zero

- [x] 6.1 [req: baseline-requires-behavior] In `evals/tests/test_runner.py`,
      add tests that `summarize` returns exit code 1 when a case's only rows
      are refused-baseline failures, while still returning 0 for an all-pass
      treatment paired with an all-fail baseline that actually ran. Run them
      and observe the refusal case fail.
- [x] 6.2 [req: baseline-requires-behavior] In `evals/run.py`, mark a refused
      run's `RunResult` so `summarize` can tell a refusal from a baseline that
      ran and failed — add a `refused` field to `RunResult` defaulting to
      False, set it on both refusal paths in `execute_case`, and make
      `summarize` return exit code 1 when any row carries a refused result,
      whatever its arm. Leave the treatment-only rule otherwise untouched.
      Confirm the task 6.1 tests pass and the whole suite stays green.

## 7. Refuse the combined arm whole

- [x] 7.1 [req: baseline-requires-behavior] In `evals/tests/test_runner.py`,
      add a test that `main(["--case","plan-csv-export","--arm","both"])`
      spawns no session for either arm — spy on `run_conversation` and assert
      it is never called — and that the exit code is non-zero. Run it and
      observe it fail: the treatment sub-run currently spawns.
- [x] 7.2 [req: baseline-requires-behavior] In `evals/run.py`, refuse the whole
      invocation for a case that cannot support a baseline — a structural
      grader, or a `prompt.md` with no `/s:` token — when the selected arm is
      `baseline` or `both`, before either arm executes. Record every requested
      run of every selected arm as refused, so no treatment session spawns on
      an invocation whose A/B cannot happen. A `treatment`-only invocation is
      unaffected and still runs such a case normally. Confirm task 7.1 passes
      and the whole suite stays green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 140 | 72.7k |
| Edit | 26 | 27.9k |
| Read | 36 | 19.7k |
| (no tool) | 0 | 10.9k |
| Agent | 5 | 5.1k |
| **Total** | 207 | 136.2k |
