# 2026-08-01 — supersession gate build: lessons

Retro from shipping `build-supersession-gate`
([PR #81](https://github.com/mikkel-bergmann/shipd/pull/81)).

## What shipped

- `spec_status.py check-base [change]` — read-only comparison of a planned
  change's deltas against the current masters: `stale-base`,
  `missing-master`, `id-collision`; exit 4 on findings.
- `/s:build` Phase 0 now syncs the branch with `origin/main`, runs the verb
  after adopting a planned change, and classifies findings as content drift
  (proceed) or superseded (stop and ask the user).

## Lessons

- **Plans go stale within hours.** Autopilot throughput already superseded one
  planned change (PR #69) before its build started; the gate mechanizes the
  base check the builder had to improvise.
- **A gate must name which checkout's state it reads.** `check-base` compares
  against the worktree's own masters, so a branch lagging main passed clean
  through the exact staleness it targets. The plan and the validator both
  missed this; the semantic review caught it, and the fix is the
  sync-with-main step before the check.
- **Version bumps collide silently.** This PR and the concurrent
  workspace-sync PR both bumped the plugin to 0.6.15. Git auto-merges
  identical hunks without conflict, so no gate fired — only a manual check
  during conflict resolution caught it (rebumped to 0.6.16). Follow-up
  (agreed, not yet planned): a CI guard requiring the version to strictly
  exceed `origin/main`'s when `plugins/s/` changes, plus duplicate detection
  on main pushes.
- **The worktree idle-window guard trips on the removing session's own
  edits.** Post-merge `worktree.sh remove` refused because this session's
  merge-resolution edits were minutes old; `--force` was needed after
  confirming the tree was clean and the PR merged. The guard could exempt the
  invoking session's own activity.
