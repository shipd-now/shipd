# worktree-remove-guard
Status: verified

## Idea

Worktree removal becomes a guarded engine verb that refuses while work is
in progress, so parallel sessions can no longer prune a worktree out from
under a live one.

### Motivation

Every session's close-out runs raw `git worktree remove` on whatever it
believes is finished, with no ownership or liveness check. Twice in one
day a parallel session deleted a worktree another session was actively
using — once mid-review-session, once under a live shell — and the
autopilot already grew tolerance for vanished worktrees (#64), which
treats the symptom. Removal needs a gate that knows what "in progress"
looks like.

### Details

- `worktree.sh remove <change>` refuses — exit 2, listing every reason —
  when the worktree has uncommitted or untracked files, anything still
  under its `.shipd/planned/`, `[~]` claims or a `.tasks.lock` in any
  planned tasks.md, or any file modified within the idle window (default
  30 minutes, `SHIPD_WORKTREE_IDLE_MINUTES` overrides). All clear → removes
  and prunes, exit 0. `--force` overrides, echoing what it overrode.
- The build skill's close-out (both call sites) and AGENTS.md say
  `worktree.sh remove`, never raw `git worktree remove`.

### Non-goals

- No process sniffing (`lsof`) — the mtime idle window is the liveness
  proxy; it is cheap, portable, and caught both real incidents.
- No PR-closing etiquette — sessions closing each other's PRs is a
  separate concern.
- No change to worktree creation or the autopilot's vanished-worktree
  tolerance (still wanted as defense in depth).

Affected capabilities: `build-spec-lifecycle` (modified). Impact:
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/skills/build/SKILL.md` (close-out sections), `AGENTS.md`,
plugin version bump.

## Implementation

- **Guard order and messages.** Checks run in the order dirty →
  unshipped → claims/lock → recent activity, accumulating every failing
  reason into one refusal report (never first-failure-only — the human
  should see the whole picture). Exit codes: 0 removed, 2 refused, 1
  usage/error — mirroring the gate engine's convention.
- **Recent-activity probe**: `find <wt> -newermt "-<N> minutes" -print
  -quit` guarded for BSD/GNU find compatibility (BSD lacks `-newermt`
  with that grammar on older versions — fall back to a `stat`-based
  newest-mtime scan capped at a few thousand files, same portability
  pattern as `mtime_of` in the statusline). Rejected: `lsof` — slow,
  non-portable, and misses shells that are merely idle between commands.
- **`--force`** performs the removal but first prints each guard it
  overrode, so a forced prune is always auditable in the session log.
- **Skill wiring**: both close-out blocks in `build/SKILL.md` swap to the
  plugin-path `remove` verb; AGENTS.md's post-merge instruction likewise.
  The `.worktree` removal in other sessions inherits the guard the next
  time their snapshots refresh — stale-snapshot sessions still run raw
  git, which is why the helper (not the prose) is the durable fix.
- Tests mirror `test_claim_task.py` style: clean-and-cold removes;
  dirty refuses; unshipped planned/ refuses; `[~]` claim refuses; fresh
  mtime refuses (fixture sets mtimes via `os.utime`, no sleeping);
  multiple reasons all listed; `--force` removes and echoes; exit codes
  asserted.

Risk: the idle window falsely blocking legitimate cleanup of a
just-merged worktree (its files are minutes old); accepted — the refusal
message says exactly how long to wait or to pass `--force`, and a merged,
archived, clean worktree fails no other guard.
