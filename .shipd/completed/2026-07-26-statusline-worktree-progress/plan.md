# statusline-worktree-progress
Status: verified

## Idea

The statusline is blind to worktrees. It resolves everything from the
session's `workspace.current_dir` and reads only that directory's
`.shipd/planned/` and `.shipd/state.json` — but this repo's own workflow develops
every change inside `.worktrees/<change>/`, so live task progress never
appears; counts only surface once the work is merged. A second bug compounds
it: git does not track empty directories, so after every merge/archive the
main checkout has no `.shipd/planned/` dir and the script's existence check
exits silently — the statusline vanishes entirely instead of reporting.

This change makes the statusline worktree-aware:

- Candidate changes come from the workspace root's `.shipd/planned/` *plus*
  `.worktrees/*/.shipd/planned/` (one level deep).
- An `active` change wins the line; the display gains `(1 of X)` after the
  spec name and `(t of Y)` after the task counts when X > 1 specs are live,
  where Y sums every live spec's task total.
- An am repo (`.shipd/` exists) with no live change reports `☕ no active
  specs` instead of going silent; only a repo with no `.shipd/` at all stays
  silent.

### Non-goals

- No `.shipd-config.json` resolution — the script stays config-blind (existing
  documented limitation); a worktree with a renamed content dir is invisible
  to the scan, consistently with the root behavior.
- No change to `use`/`current` selection semantics or `state.json` shape.
- No recursion beyond one level under `.worktrees/`, and no scanning of
  arbitrary sibling checkouts.

Affected capabilities: `statusline` (modified). Impact:
`plugins/s/integrations/statusline.sh`,
`plugins/s/skills/build/tests/test_statusline.py`, the README's statusline
blurb, plugin version bump.

## Implementation

- **Candidate pool.** `<ws>/.shipd/planned/<c>` for each change dir, plus
  `<ws>/.worktrees/<w>/.shipd/planned/<c>` via a bounded `find`-free glob loop
  (bash 3.2: plain `for d in "$ws"/.worktrees/*/.shipd/planned/*/`). Cost stays
  a handful of `stat`/`sed`/`grep` calls — acceptable for a statusline
  refresh.
- **Pick rule, in precedence order.** (1) the sole candidate whose `plan.md`
  status is `active`; (2) among several `active`, the one whose `tasks.md`
  mtime is newest (a running build ticks its checklist — mtime tracks the
  live one); (3) no active: the workspace root's `state.json` selection when
  it resolves to a root candidate; (4) a sole candidate overall; (5) several
  candidates, none pickable → `☕ <n> specs · none selected` with n = X.
  Rejected: preferring the root selection over an active worktree change —
  the user's rule is explicit that a running spec owns the line.
- **Bracket grammar.** Only when X > 1: name segment renders
  `<name> (1 of X)`; the tasks segment renders `<d>/<t> (<t> of <Y>)`, Y =
  the sum of checkbox totals across all candidates that carry a `tasks.md`.
  When the shown change has no `tasks.md`, the tasks segment (and its
  bracket) is omitted as today.
- **Silence semantics.** `[ -d "$ws/.am" ]` becomes the am-project gate; a
  missing or empty `planned/` (root and worktrees) renders
  `☕ no active specs`. A directory with no `.shipd/` prints nothing, exit 0 —
  unchanged for non-am repos.
- **Constraints held.** bash 3.2 (no mapfile/assoc arrays), no runtimes
  spawned, read-only, one output line, bare U+2615. mtime read via
  `stat -f %m` on Darwin with `stat -c %Y` fallback, guarded so a missing
  `stat` variant degrades to candidate order rather than erroring.

Risk: glob loops over `.worktrees/` when it holds many stale worktrees could
slow the refresh — bounded by the one-level glob and no per-file subprocess
beyond the existing sed/grep pattern; stale worktrees are also routinely
removed by the workflow's close-out step.
