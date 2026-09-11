<!-- doc-type: concept -->

# The supersession gate

A planned change can go stale fast. Between `/s:plan` and `/s:build`, other PRs
may merge work that already implements some or all of the plan. An autopilot
run is the usual culprit. Building anyway would clobber newer spec wording and
re-do shipped work. The **supersession gate** catches that mechanically, before
any execution sub-agent spawns.

## What build does automatically

When `/s:build` adopts an already-planned change, Phase 0 runs three steps:

1. **Sync the branch with its base** — `git fetch origin main && git merge origin/main`.
   The check compares against the worktree's own masters, so a lagging branch
   catches up first. A merge conflict here is itself a supersession signal, and
   build surfaces it to you.
2. **Run the base check** — the status CLI's `check-base` verb.
3. **Act on the result**, which takes one of three shapes.

The three outcomes are:

- **Clean** — build proceeds, and you see nothing.
- **Findings, classified as content drift** — the masters moved for unrelated
  reasons, and the plan's substance is still unbuilt. Build proceeds, and
  carries the findings into plan review.
- **Findings, classified as superseded** — a merged PR already implemented the
  plan's substance. Build **stops** and asks you whether to abandon the change
  or re-scope it to what remains. It executes nothing.

## Running the check yourself

```
python3 plugins/s/skills/build/scripts/spec_status.py check-base [change]
```

The verb compares the change's delta specs against the current master library.
It reads only, and it defaults to the currently selected change. It prints one
line per finding:

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

Exit codes: `0` clean, `4` findings. Those stay distinct from `1` for a general
error and `3` for a guard refusal, so scripts can gate on the verb directly.

A clean check cannot *prove* that nothing superseded the plan. A merge may
never have touched the same requirement ids, so build's discovery read remains
the judgment backstop. The verb mechanizes the common case: deltas colliding
with masters that moved.
