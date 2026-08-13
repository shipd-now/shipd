# Tasks — eval-worktree-grading

## 1. Worktree-aware grading

- [x] 1.1 [req: deterministic-grading] In `evals/tests/`, add failing unit tests for `grade()` over hand-built scratch fixtures: a root-only lint-clean `ready` change passes (regression); a worktree-only change at `<scratch>/.worktrees/<change>/.shipd/planned/<change>/` passes; one change in each location fails naming both paths; no change anywhere fails with a message naming both inspected locations; a worktree change at `Status: draft` fails on the ready assertion.
- [x] 1.2 [req: deterministic-grading] In `evals/run.py`, rewrite `grade()` per the plan: candidate glob over root + one worktree level, exactly-one across the union, lint `--root` at the containing tree, `Status: ready` read from the found plan, widened failure messages. Tests from 1.1 pass.

## 2. Verification

- [x] 2.1 [req: *] Barrier: `uvx pytest evals/tests/ -q` green; the engine unittest suite untouched and green; live run `python3 evals/run.py` — both `/s:plan` cases must pass with the sessions' worktree-emitted changes graded correctly.
