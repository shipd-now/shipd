# The supersession gate

A planned change can go stale fast: between `/s:plan` and `/s:build`,
other PRs — especially an autopilot run — may merge work that already
implements some or all of the plan. Building anyway would clobber newer spec
wording and re-do shipped work. The **supersession gate** catches this
mechanically before any execution sub-agent spawns.

## What build does automatically

When `/s:build` adopts an already-planned change, Phase 0 now:

1. **Syncs the branch with its base** — `git fetch origin main && git merge
   origin/main`. The check compares against the worktree's own masters, so a
   lagging branch must catch up first; a merge conflict here is itself
   treated as a supersession signal and surfaced to you.
2. **Runs the base check** — `spec_status.py check-base <change>`.
3. **Acts on the result:**
   - **Clean** → build proceeds; you see nothing.
   - **Findings, classified as content drift** — the masters moved for
     unrelated reasons, the plan's substance is still unbuilt → build
     proceeds, reconciling the findings during plan review.
   - **Findings, classified as superseded** — a merged PR already implemented
     the plan's substance → build **stops** and asks you whether to abandon
     the change or re-scope it to what remains. Nothing is executed.

## Running the check yourself

```
python3 plugins/s/skills/build/scripts/spec_status.py check-base [change]
```

Compares the change's delta specs against the current master library
(read-only; defaults to the currently selected change). One line per finding:

| Finding | Meaning |
| --- | --- |
| `stale-base` | A MODIFIED/REMOVED entry's `base:` hash no longer matches the master — the requirement changed since the plan was written (expected/actual hashes are printed). |
| `missing-master` | The entry's requirement id — or the whole capability master — no longer exists. |
| `id-collision` | The plan ADDs a requirement id the master already has — the strongest signal the work is already merged. |

```
$ spec_status.py check-base my-change
build-context-gate/supersession-gate: id-collision
spec-status/status-cli: stale-base (expected 668ed5dbee15, actual 969a22088565)
check-base: 2 finding(s).
```

Exit codes: `0` clean, `4` findings (distinct from `1` general error and `3`
guard refusal), so scripts can gate on it directly.

A clean check can't *prove* nothing superseded the plan (a merge may not have
touched the same requirement ids) — build's discovery read remains the
judgment backstop. The verb mechanizes the common case: deltas colliding with
masters that moved.
