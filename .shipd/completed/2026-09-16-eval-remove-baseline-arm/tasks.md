## 1. Repair the handoff grader

- [x] 1.1 [req: handoff-grading] In `evals/tests/test_runner.py`, add tests for
      the authored-content comparison, all built through the real
      `run.assemble_scratch`: engine scaffolding created outside the authored
      locations passes; a new file under `src/` fails naming it; a new file
      under a scratch-root `.shipd/planned/<name>/` fails naming it; the same
      written inside a `.worktrees/<name>/.shipd/planned/<name>/` also fails; a
      rewritten shipped test still fails because it was in the snapshot. Run
      them and observe the scaffolding and worktree cases fail.
- [x] 1.2 [req: handoff-grading] In `evals/run.py`, replace `grade_handoff`'s
      whole-tree comparison with the authored-content rule: report the first
      snapshotted file that was modified or deleted, then the first new file
      appearing under `src/` or under any `.shipd/verified/` or
      `.shipd/planned/` directory found by walking the scratch (so a worktree is
      covered), and treat every other new file as tolerated. Keep the
      `__pycache__`, `.git`, and `eval-transcript*.json` exclusions. Confirm the
      task 1.1 tests pass.
## 1b. Drive each grader with its own gate and reply

- [x] 1b.1 [req: grader-selected-driving] In `evals/tests/test_runner.py`, add
      tests driving `run_conversation` with an injected turn runner: a handoff
      case runs exactly one turn and is sent no reply; a structural case keeps
      the structural gate and the plan-specific reply; a behavior case keeps its
      own gate and reply; and a case whose grader has no gate or reply defined
      is recorded as failed naming that grader. Run them and observe the handoff
      and unknown-grader cases fail.
- [x] 1b.2 [req: grader-selected-driving] In `evals/run.py`'s
      `run_conversation`, replace the `behavior`-versus-everything-else branch
      with a per-grader selection covering `structural`, `behavior`, and
      `handoff`. A handoff case sends turn 1 and returns without resuming; an
      unrecognized grader returns a failure naming it rather than borrowing
      another grader's gate or reply. Confirm the task 1b.1 tests pass.
- [x] 1b.3 [req: handoff-grading] Run
      `python3 evals/run.py --case fix-spec-wrong --runs 1` and confirm it now
      PASSES, and that the kept scratch holds exactly one `eval-transcript.json`
      with no `-turn2` sibling. This spawns one real session and costs model
      spend; run it exactly once. If it fails, report the failure and the
      session's final text rather than adjusting the grader to make it pass.

## 2. Remove the arm from the session invocation

- [x] 2.1 [req: arm-selection] In `evals/tests/test_runner.py`, delete the tests
      that exercise the removed surface — the baseline-arm command construction,
      `baseline_prompt`, `_arm_refusal`, the refusal dispatch, and the
      combined-arm whole-invocation refusal. Keep every test that covers the
      structural, behavior, and handoff graders, `read_expect`, and case
      discovery.
- [x] 2.2 [req: arm-selection] In `evals/run.py`, remove the `arm` parameter
      from `_run_turn`, `run_conversation`, and `execute_case`, so the session
      command always carries `--plugin-dir` and turn 1 always sends the case's
      `prompt.md` unmodified.
- [x] 2.3 [req: derived-baseline-prompt] In `evals/run.py`, delete
      `baseline_prompt` and any helper that exists only to serve it.
- [x] 2.4 [req: baseline-requires-behavior] In `evals/run.py`, delete
      `_arm_refusal`, `_refused_results`, the `RunResult.refused` field, and
      `main`'s `invocation_refusal` computation, restoring `execute_case`'s
      sanity-check and grading dispatch to run for every case.

## 3. Restore per-case reporting

- [x] 3.1 [req: pass-rate-reporting] In `evals/tests/test_runner.py`, delete the
      per-arm and refusal `summarize` tests, and confirm the pre-A/B
      `SummarizeTests` still pass unchanged against a case-name-keyed mapping.
- [x] 3.2 [req: pass-rate-reporting] In `evals/run.py`, key `summarize`'s input
      by case name, render one row per case with no arm label, and derive the
      exit code from every case's pass-rate. In `main`, remove the `--arm`
      argument and the arm loop, calling `execute_case` once per case.

## 4. Verify and document

- [x] 4.1 [req: arm-selection] Run `python3 -m unittest discover -s evals/tests`
      and confirm the suite passes with no third-party package installed, and
      that `grep -rn "arm\|baseline_prompt\|refused" evals/run.py` reports no
      surviving reference to the removed concepts outside prose.
- [x] 4.2 [req: pass-rate-reporting] Run
      `python3 evals/run.py --case plan-csv-export --runs 1` and confirm the
      summary prints one unlabelled row for the case. This spawns one real
      session; run it exactly once.
- [x] 4.3 [req: arm-selection] In `AGENTS.md`'s `## Evals` section, delete the
      `--arm` documentation and describe the harness as a single-arm regression
      gate over the three graders. Record that a handoff case is never resumed,
      because its correct outcome is that the session stops, and that each
      grader selects its own gate and reply. State that `fix-spec-wrong` passes:
      `/s:fix` diagnoses the wrong contract and stops, which the harness
      previously overrode by resuming it with a reply instructing it to emit,
      lint, and promote a change. Do not describe any case as shipping red.
