# eval-headless-oracle-default — tasks

## 1. The pure judgement

- [x] 1.1 [req: oracle-default-grading] In `evals/tests/test_runner.py`, add
      tests for `run.judge_oracle_default` against literal `plan.md` text: a
      ready plan whose one `INSUFFICIENT` entry is answered by `USER` passes; a
      ledger with no `**Verdict:**` field fails naming the verdict; an
      `INSUFFICIENT` entry with an empty `**Answer:**` fails naming the entry;
      a non-zero lint exit and a non-zero gate exit each fail naming their
      point; a `draft` plan fails naming the gate. Run them and observe them
      fail.
- [x] 1.2 [req: oracle-default-grading] In `evals/run.py`, add
      `judge_oracle_default(plan_text, lint_exit, gate_exit, lint_output,
      gate_output)` and the ledger parser it uses, reading no file and running
      no process. Confirm the task 1.1 tests pass.

## 2. Wire the grader

- [x] 2.1 [req: oracle-default-grading] In `evals/run.py`, add
      `grade_oracle_default(scratch_dir, host_repo)`: find the one change with
      `_collect_candidates`, run `spec_lint.py` and `spec_gate.py --check`
      against its tree, read its `plan.md`, and return the judge's result. Add a
      test building a lint-clean ready change with a ledger and asserting it
      passes.
- [x] 2.2 [req: case-grader-selection] In `evals/run.py`, add `oracle-default`
      to `RECOGNIZED_GRADERS`, and add a `read_expect` test for it.
- [x] 2.3 [req: grader-selected-driving] In `evals/run.py`, drive an
      `oracle-default` case in `run_conversation` with the structural gate and
      `GOAHEAD_REPLY`, and dispatch it to `grade_oracle_default` in
      `execute_case`. Add a driving test asserting the structural gate and
      reply.

## 3. The case

- [x] 3.1 [req: oracle-default-grading] Create
      `evals/cases/plan-oracle-default/` with `expect.json` declaring
      `{"grader": "oracle-default"}`, a `fixture/` holding the report CLI
      script under src, a verified `reporting` spec, empty `planned/` and
      `completed/` directories, and a lint-clean wiki store whose one page
      covers flag naming and never mentions sorting, and a `prompt.md` asking
      `/s:plan` for a `--sort` flag whose bare-flag column is undecided.
- [x] 3.2 [req: oracle-default-grading] Without spawning a session, confirm
      the fixture's wiki lints clean with `spec_lint.py --wiki` and that
      `oracle-lookup` on the decision's terms finds no sentence taking a
      position on the sort column.

## 4. Verify and document

- [x] 4.1 [req: oracle-default-grading] In `AGENTS.md`'s `## Evals` section,
      document the `oracle-default` grader, its four points, its driving, and
      `evals/cases/plan-oracle-default` as its case.
- [x] 4.2 [req: oracle-default-grading] Run `python3 -m unittest discover -s
      evals/tests` and confirm the whole suite passes with no third-party
      package installed.
