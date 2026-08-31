# worktree-guard-fixes
Status: verified
Theme: reliability

## Idea

Stop `worktree.sh remove` refusing every legitimate close-out, and stop
`prune-branches` mis-reporting a squash-merged branch as unmerged when the base
moved before the branch landed.

### Motivation

`/s:build`'s documented close-out runs `remove` seconds after its own merge
commit, so the idle-window guard fires on the removing session's own writes —
three refusals out of three last session, each overridden with `--force`; and
`prune-branches` left a fully shipped branch behind because its patch-identity
probe cannot see a squash applied onto a base that had moved.

### Details

- In `plugins/s/skills/build/scripts/worktree.sh`, run the idle-window probe
  only while the worktree's tree is dirty, so a clean worktree removes however
  recently its files were written.
- In the same file, add a second merged-ness probe to `prune-branches`: where
  the content probe reports not-merged, treat an absent remote-tracking ref as
  merged, refreshing refs with a pruning fetch first.
- Fall back to the content probe alone where no remote is configured or the
  refresh fails, so the verb never depends on the network.
- Cover both in `plugins/s/skills/build/tests/test_worktree.py`, whose harness
  gains a local bare repository to act as `origin`.
- Bump the plugin version.

Affected capability: `build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No change to the other three removal guards — uncommitted or untracked
  files, an unshipped `.shipd/planned/` change, and `[~]` claims or a
  `.tasks.lock` — nor to their reason lines.
- No removal of the idle probe or of `SHIPD_WORKTREE_IDLE_MINUTES`.
- No change to `remove`'s exit codes, `--force` semantics, or the create and
  `--fresh` flows.
- `prune-branches` still deletes nothing outside `change/*` and never a
  checked-out branch.
- No new dependency on `gh` or on any GitHub API; the second probe reads git
  refs only.

## Implementation

- **The idle probe becomes subordinate, deliberately.** Gating it on a dirty
  tree makes it non-decisive: a dirty tree already refuses through the
  uncommitted-files guard, so the probe can now only add a second reason line
  beside that one. That is accepted rather than worked around — a clean
  worktree with no planned change and no claims is genuinely
  indistinguishable from a finished close-out, so there is nothing left for
  the probe to protect. Rejected: deleting the probe and its environment
  variable, which changes the same behavior while dropping a documented knob;
  and excluding specific paths, which the evidence disproves — the refusal
  named `plugins/s/skills/plan`, an ordinary edited source directory, not
  `.git/` or the content directory.
- **Reuse the dirty check already computed.** `worktree.sh:180-183` runs
  `git -C "$WORKTREE" status --porcelain` for guard 1; the idle probe reads
  that same result rather than shelling out again.
- **Two probes, in order, for merged-ness.** The existing content probe stays
  first: it is exact when it fires and needs no remote. The second probe —
  an absent remote-tracking ref — is what a squash merge that deletes its
  remote branch leaves behind, and it is the only signal that survives the
  base moving. Rejected: `git merge-tree --write-tree`, which was run against
  the real failing branch and also reported not-merged, because a later merge
  had bumped `plugin.json` to a version the branch also bumped and the merge
  conflicts on that line.
- **Why the content probe fails, precisely.** It replays the branch's tree on
  the merge-base and asks `git cherry` whether the base carries that patch.
  When commits land on the base between fork and merge that touch the same
  files, the squash commit's diff is computed against different content, so
  the patch identities differ. Verified against the real tip `2062787`:
  merge-base `01fc6fe`, `cherry` returned `+ a355885`, i.e. not merged, while
  the branch was fully shipped in `b135bc7`.
- **The refresh is required, not optional.** `fetch.prune` is unset here and
  `git pull` does not prune, so stale remote-tracking refs linger:
  `git fetch --prune --dry-run` listed four refs still present for branches
  whose remotes were long deleted. Without the refresh the second probe reads
  stale state and never fires.
- **Failure is conservative.** Where no remote is configured, or the fetch
  fails (offline, unreachable host), the verb keeps the content probe's
  verdict and prunes nothing extra — the same outcome as today, never a
  wrongly deleted branch.

Risk: a branch merged **without** deleting its remote branch keeps its
remote-tracking ref, so the second probe will not fire for it and the branch
stays. Confirmed live: `change/oracle-naming-sweep`'s PR #108 is merged yet its
`origin/` ref survives. This is a false negative in the safe direction —
identical to today's behavior — and the verb reports it as kept, so nothing is
silently destroyed.

Risk: the pruning fetch reaches the network from a helper previously
documented as git-only. Bounded by the fallback above, and by running the
fetch only where a remote is actually configured.
