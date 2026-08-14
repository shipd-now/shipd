# skill-evals — tasks

## 1. Runner

- [x] 1.1 [req: eval-case-layout, deterministic-grading, pass-rate-reporting]
      Add `evals/tests/test_runner.py` (pytest, stdlib + pytest only) covering:
      case discovery over a temp `cases/` tree (valid case found; directory
      missing `prompt.md` or `fixture/` skipped), `--case` filtering, grading
      of a prebaked scratch tree (one lint-clean `Status: ready` change →
      pass; zero changes → fail; two changes → fail; `Status: draft` → fail),
      and pass-rate/exit-code aggregation (2/3 passes → non-zero exit). Run it
      and observe it fail — `evals/run.py` does not exist yet.
- [x] 1.2 [req: eval-case-layout] Create `evals/run.py` (Python 3 stdlib
      only): argparse CLI with `--case`, `--runs` (default 1), `--claude-bin`
      (default `claude`), `--keep-scratch`; implement case discovery over
      `evals/cases/` returning case name, prompt path, fixture path.
- [x] 1.3 [req: headless-skill-run] In `evals/run.py`, implement scratch
      assembly: copy the fixture to a `tempfile.mkdtemp` directory, overwrite
      `am/README.md` with the host repo's `am/README.md`, then `git init`,
      `git add -A`, and an initial commit inside the scratch dir.
- [x] 1.4 [req: headless-skill-run] In `evals/run.py`, implement session
      invocation: run `<claude-bin> -p <prompt text> --plugin-dir
      <host>/plugins/am --permission-mode bypassPermissions --output-format
      json` with `cwd=<scratch>` and a 20-minute `subprocess` timeout; write
      captured stdout to `<scratch>/eval-transcript.json`; on timeout or
      non-zero exit, mark the run failed and continue with remaining runs.
- [x] 1.5 [req: deterministic-grading] In `evals/run.py`, implement grading:
      list `am/planned/` in the scratch dir (assert exactly one change
      directory), run the host repo's
      `plugins/s/skills/build/scripts/spec_lint.py <change> --root <scratch>`
      (assert exit 0), and read the change's `plan.md` (assert a
      `Status: ready` line); name the first failing assertion in the run
      result.
- [x] 1.6 [req: pass-rate-reporting] In `evals/run.py`, implement the run
      loop and summary: execute each case `--runs` times, print a per-case
      `passed/runs` table, exit non-zero if any executed case has a pass-rate
      below 1.0; delete scratch dirs unless `--keep-scratch`. Confirm
      `evals/tests/test_runner.py` from 1.1 now passes.

## 2. Cases

- [x] 2.1 [P1] [req: eval-case-layout] Add case `evals/cases/plan-csv-export/`:
      `fixture/` is a minimal repo with a tiny Python CLI (`src/report.py`
      printing fixed rows) and an `am/` layout (`am/planned/.gitkeep`, empty
      `am/verified/`, placeholder `am/README.md` — replaced at run time);
      `prompt.md` asks `/s:plan` to plan a `--csv` export flag for the
      report command.
- [x] 2.2 [P1] [req: eval-case-layout] Add case `evals/cases/plan-new-capability/`:
      `fixture/` like 2.1 but with one existing verified capability
      (`am/verified/reporting/spec.md` with a single requirement) so the
      session must add a *new* capability alongside an existing one without
      touching it; `prompt.md` asks `/s:plan` to plan a small unrelated
      feature (a `--version` flag).
- [x] 2.3 [req: *] End-to-end verification: from the repo root run
      `python3 evals/run.py --keep-scratch`, observe both cases execute real
      headless sessions and grade; fix any harness defects surfaced (not
      model-behavior variance) and re-run until the harness itself operates
      correctly end to end.

## 3. Docs

- [x] 3.1 [req: *] Add an "Evals" section to `AGENTS.md`: what `evals/` is,
      how to run it (`python3 evals/run.py [--case ...] [--runs N]`), that
      runs cost real model spend and stay out of the `ci` check, and that
      skill-touching changes should get a local eval run before shipping.
