# eval-worktree-grading
Status: verified

## Idea

The eval grader inspects only the scratch root, so sessions that
correctly follow the worktree convention fail every eval — this change
teaches grading to look where the workflow actually puts changes.

### Motivation

Both `/s:plan` eval cases fail with "no change directory under
`.shipd/planned/`" — yet the graded sessions succeed. Since the worktree
helper moved into the plugin, headless plan sessions correctly follow the
one-change-one-worktree convention inside eval scratch repos, emitting
the change into `<scratch>/.worktrees/<change>/.shipd/planned/` on its
branch. The grader still inspects only the scratch root, so every eval
fails against sessions behaving exactly as instructed — the harness
drifted behind the convention it exists to test.

### Details

- `grade()` collects candidate changes from the scratch root's
  `.shipd/planned/` **and** one level of `.worktrees/*/.shipd/planned/`,
  requires exactly one across both, lints it with `--root` pointing at
  wherever it lives, and reads `Status: ready` from that plan.
- Failure messages name where the grader looked, so the next drift is
  diagnosable from the runner output alone.

### Non-goals

- No changes to session driving, resume grading cadence, or the case
  format — only the structural grade's search space.
- No multi-change tolerance: exactly one change total, wherever it lives,
  remains the bar.
- No teaching the grader other conventions (branches without worktrees,
  renamed content dirs) — default `.am` only, matching the fixtures.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`
(`grade` and its failure messages), `evals/tests/` unit tests. No plugin
code touched, no version bump (the harness is repo-local).

## Implementation

- **Candidate scan mirrors the statusline's**: glob
  `<scratch>/.shipd/planned/*/` plus `<scratch>/.worktrees/*/.shipd/planned/*/`;
  the graded root is the scratch dir for root candidates and the worktree
  dir for worktree candidates, so `spec_lint.py --root` and the
  `plan.md` read both target the tree the change actually lives in.
  Rejected: normalizing by copying the worktree change to the root —
  grading should observe, never mutate the scratch.
- **Exactly-one across the union**: zero → "no change directory under
  .shipd/planned/ (scratch root or worktrees)"; more than one → the paths
  are listed. The pass condition and `Status: ready` check are unchanged
  in meaning.
- Unit tests in `evals/tests/` build scratch fixtures for: root-only
  change (passes, regression), worktree-only change (passes — the new
  case), one of each (fails, both named), none (fails with the widened
  message).

Risk: a worktree change lints against its own tree's masters, which in
eval fixtures are the copied fixture masters on the branch — identical to
the root's by construction; guarded by the live barrier run of both real
cases.
