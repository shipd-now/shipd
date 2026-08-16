# worktree-branch-hygiene
Status: verified
Epic: pipeline-hardening

## Idea

Make `worktree.sh` branch reuse loud (an explicit notice with ahead/behind
counts), add a `--fresh` flag that guarantees epic-close derivations a fresh
branch, and add a guarded `prune-branches` verb that deletes local `change/*`
branches whose content is already merged into the base branch.

### Motivation

`worktree.sh`'s create path silently adopts a pre-existing `change/<name>`
branch and still prints "Created worktree", which mis-derived an epic status
when an epic-close ran on a stale local branch — and squash-merge PRs delete
only the remote branch, so ~30 merged local `change/*` branches have
accumulated with no tool to reclaim them (epic `pipeline-hardening`).

### Details

- Both reuse arms of the create path (worktree reused; branch re-attached)
  print an explicit reuse notice with the branch's ahead/behind counts against
  the base branch; only true creation says "Created".
- New `--fresh` flag: errors when `.worktrees/<name>` exists or the branch
  exists unmerged; deletes and recreates a branch whose content is merged.
- New `prune-branches` verb: deletes local `change/*` branches whose content
  is merged into the base (squash merges included), never the current or
  checked-out ones, listing every deletion and every branch kept.
- The build skill's Phase 7 epic-close step and `autopilot.py`'s
  `_default_sync_fn` create their `epic-close-<slug>` worktree with `--fresh`.

Affected capabilities: `build-spec-lifecycle` (modified),
`epic-autopilot` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/SKILL.md`, `AGENTS.md`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No refusal of branch reuse: reusing an in-flight change's branch after
  worktree removal is legitimate and stays idempotent (epic decision).
- No remote operations: prune-branches touches local branches only and never
  fetches, pushes, or deletes remote refs.
- No changes to the `remove` verb's guards or to the reclaim path in
  `autopilot.py` (`stale-worktree-reclaim` behavior is untouched).
- No pruning of non-`change/*` branches.

## Implementation

- **Base branch = the root checkout's checked-out branch**, resolved once with
  `git symbolic-ref -q --short HEAD` at the repo root (the cwd the helper
  already requires). Rejected: `origin/HEAD` — the helper "assumes nothing
  about the repository beyond git itself" and the test fixtures have no
  remote. On a detached root HEAD the reuse notice omits its counts (printing
  the notice without them), while `--fresh` and `prune-branches` error out —
  they cannot judge merged-ness without a base.
- **Merged-content probe** (shared by `--fresh` and `prune-branches`): a
  branch counts as merged when `git merge-base --is-ancestor <branch> <base>`
  succeeds, or when the squash probe flags it — `ancestor=$(git merge-base
  <base> <branch>)`, `tree=$(git rev-parse <branch>^{tree})`,
  `tmp=$(git commit-tree "$tree" -p "$ancestor" -m probe)`, and `git cherry
  <base> "$tmp"` starts with `-`. No merge-base at all means not merged.
  Verified live: `git branch --merged` misses a squash-merged branch, the
  cherry probe prints `-` for it and `+` for an unmerged one.
- **Reuse notice**: ahead/behind from `git rev-list --left-right --count
  <base>...<branch>` (left = behind, right = ahead, verified live printing
  `1 1`). The reuse arm prints `Reusing existing worktree … on branch …
  (ahead N, behind M vs <base>).`, the attach arm `Attached worktree … to
  existing branch … (ahead N, behind M vs <base>).`; the fresh-creation arm
  alone keeps `Created worktree …`. The "Next steps" block stays on all arms.
- **`--fresh` parsing**: accepted after the change name
  (`worktree.sh <name> --fresh`), mirroring `remove`'s trailing-flag loop.
  Order: worktree exists → error exit 1 (fresh means fresh — never reuse);
  branch exists unmerged → error exit 1 naming the branch, nothing changed;
  branch exists merged → `git branch -D`, print what was deleted, then create
  branch and worktree anew.
- **`prune-branches` verb**: dispatched like `remove`. Enumerates
  `git for-each-ref --format='%(refname:short)' refs/heads/change`; skips the
  root checkout's current branch and any branch named by a `branch
  refs/heads/…` line of `git worktree list --porcelain` (verified live to name
  checked-out branches); deletes merged ones with `git branch -D` printing
  `pruned: <branch>`, prints `kept: <branch> (<reason>)` for the rest, ends
  with a summary count, exits 0 even when nothing prunes. Rejected: `git
  branch -d` — it cannot see squash merges, which are the whole problem.
- **Consumers**: `plugins/s/skills/build/SKILL.md` Phase 7 runs
  `worktree.sh epic-close-<slug> --fresh`; `_default_sync_fn` in
  `plugins/s/skills/build/scripts/autopilot.py` appends `--fresh` to its
  `WORKTREE_SH` invocation (its tests fake `_run_command`, so the argv is
  directly assertable). `AGENTS.md`'s after-merge paragraph names
  `prune-branches`; its epic-derivation paragraph names `--fresh`.
- **Constraints**: bash 3.2-safe (no mapfile, no associative arrays), matching
  the script's existing header; engine change ships with tests in
  `plugins/s/skills/build/tests/` (constitution); plugin version bump
  0.6.120 → 0.6.121 in `plugins/s/.claude-plugin/plugin.json`.
- **Risk**: the squash probe creates throwaway commit objects via
  `git commit-tree`; they are unreferenced and garbage-collected, never
  touching any ref. Risk: `--fresh` deleting a branch someone wanted — guarded
  by the merged-only rule; unmerged content is never deleted.
