# worktree-sweep
Status: verified
Theme: developer-experience

## Idea

Add a `sweep` verb that reclaims merged worktrees and their branches, and run it
opportunistically whenever a new worktree is created.

### Motivation

`worktree.sh remove` never consults merged-ness and `prune-branches` has no
caller at all, so a worktree outlives its merged PR whenever the build session
that created it does not reach its close-out — under `pr-mode: draft`, or after
a crash. Merged local `change/*` branches then accumulate with nothing to
reclaim them.

### Details

- Add `sweep [--dry-run]` to `worktree.sh`: remove every worktree whose branch
  already merged and whose existing removal guards pass, report the rest, then
  run the existing branch prune.
- Extract the `remove` guard chain into a shared helper both verbs call, so the
  sweep never reimplements a guard.
- Dispatch `sweep` through `worktree.py` and call it after a successful create,
  gated on a config key.
- Add three layered config keys with env-var overrides, and surface them to the
  bash helper as `config-show` lines.

Affected capabilities: `build-spec-lifecycle` (modified), `worktree-hooks`
(modified), `shipd-config` (modified), `spec-status` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh`, `worktree.py`, `spec_common.py`,
`spec_status.py`, `plugins/s/skills/build/references/shipd.config.example.json`,
`AGENTS.md`. No new dependencies; `bin/shipd` is unchanged because its
`worktree` entry already forwards every argument verbatim.

### Non-goals

- No removal of an unmerged worktree, however idle — abandoned work is reported
  on a `stale:` line and never touched.
- No interactive prompt; the sweep runs unattended and silently where nothing
  changed.
- No new skill or slash command, and no new `bin/shipd` verb.
- No change to what the existing `remove` guards check.

## Implementation

- **`sweep` is a verb on `worktree.sh`, not a skill.** The job is deterministic
  git mechanics over guards that already live there. Rejected: an `/s:clean`
  skill — it would add a permanent roster entry and a SKILL.md to wrap a shell
  loop.
- **Merged-ness gates removal, using the two probes `prune-branches` already
  consults**: `branch_is_merged` (squash-aware content probe), then
  `branch_remote_ref_gone`. Rejected: treating "all guards pass" as a proxy for
  merged — the guards pass on abandoned-but-unmerged worktrees.
- **A branch with no commits ahead of the base is never swept.** A freshly
  created branch is an ancestor of the base, so `branch_is_merged` returns true
  and every guard passes on it — without this precondition the create-path
  sweep would delete the worktree it just created. Rejected: an `--except
  <name>` flag — it guards only the one caller that remembers to pass it.
- **The sweep reuses the `remove` guard chain, extracted into
  `collect_remove_reasons`.** `cmd_remove` and `cmd_sweep` both call it, so a
  guard added later applies to both. The sweep never passes `--force`.
- **The sweep always exits 0**, whether it removed anything or refused
  everything. It is opportunistic housekeeping on the create path; a housekeeping
  failure must never fail a worktree creation. A detached root HEAD is the one
  exception `prune-branches` already errors on, so the sweep skips the branch
  prune there rather than inheriting its non-zero exit.
- **Output is asymmetric by caller.** The explicit verb prints a full
  `swept:`/`kept:`/`stale:` report; the create-path call prints only lines for
  what it actually changed, so `worktree <change>` stays quiet on a clean repo.
- **Three layered config keys**, snake_case like `completed_retention_days`:
  `worktree_sweep` (boolean, default `true`), `worktree_idle_minutes` (integer,
  default 30), `worktree_stale_days` (integer, default 7). Precedence is env var
  > config layer > built-in default, so `SHIPD_WORKTREE_IDLE_MINUTES` keeps
  working as the ad-hoc override and gains `SHIPD_WORKTREE_STALE_DAYS` as its
  symmetric partner.
- **Bash reads the keys through `config-show`**, the seam `worktree.sh` already
  uses for `content-dir:` and `store:`, with the same fail-safe fallback to the
  built-in defaults on any resolution failure. Rejected: a second resolution
  path in bash — it would drift from the layered loader.
- **The create-path sweep runs the full branch prune, fetch included.**
  `prune-branches` already falls back to the content probe when no remote is
  configured or the fetch fails, so it never depends on the network, and the
  create path may already run `post-worktree-scripts` far slower than a fetch.

Risk: the sweep removes a worktree a parallel session is using. Guarded by the
unchanged guard chain — a dirty tree, an unshipped planned change, a `[~]` claim,
or a `.tasks.lock` all still refuse, and the sweep never forces.

## Questions and answers

### Q1: What should the sweep do with a clean, unmerged, long-idle worktree?
- **Question:** Should the sweep report, ignore, prompt on, or remove a worktree
  whose branch is unmerged but whose guards all pass? Options: (1) report it on
  a `stale:` line and never touch it; (2) ignore it entirely; (3) prompt when a
  terminal is attached; (4) remove it, since the branch preserves the commits.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Report only — option 1. The sweep prints a `stale:` line naming
  the worktree and how long its branch has been idle, and removes nothing.
  Deleting a checkout of unshipped work is not worth the reclaimed disk, and a
  prompt inside worktree creation defeats the point of making creation fast.
  The staleness threshold is 7 days, overridable from a config layer as well as
  from the environment.
- **Queued:** none

## Notes

The read rung was consulted before this question reached the user and held no
position: the personal memory store does not exist on this machine, and the
workspace wiki carries no page matching worktree, cleanup, or staleness.
