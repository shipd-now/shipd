# claim-wait-foreground
Status: verified

## Idea

Lower the coordinator's `claim --wait` default below the harness foreground budget, and close the two contract gaps that let an unwatched claim stall a build.

### Motivation

`claim_task.sh:103` defaults `--wait` to 600 seconds while the Bash tool's foreground budget is 120, so the invocation `sub-agent.md:91` prescribes is auto-backgrounded — which `sub-agent.md:98` forbids in the very next bullet. A worker cannot obey both, and in the drive-skill build this stalled every builder behind a task held `[~]` by nobody.

### Details

- Lower the `--wait` default from 600 to 90 seconds, and sync the four sites that name it.
- Forbid ending a turn while still holding a claim: the worker completes or releases first.
- Give the orchestrator an explicit stale-claim check between fan-out rounds.

Affected capabilities: `build-task-coordination` (two requirements modified). Impact: `plugins/s/skills/build/scripts/claim_task.sh`, `plugins/s/agents/sub-agent.md`, `plugins/s/skills/build/SKILL.md`, the two guarding test modules, and the plugin version bump.

### Non-goals

- No auto-reclaim in `claim`. A slow-but-alive worker must never be robbed of its task; `release --stale` stays the deliberate, operator-driven path.
- No change to the `--wait` retry interval, the lock protocol, the claim record format, or `tasks.md` grammar.
- No new verb, and no change to the empty-stdout-exit-zero contract a timeout already honors.
- No attempt to detect backgrounding at runtime — the fix is to make the documented call fit the budget, not to police the harness.

## Implementation

- **90 seconds, not 600.** The Bash tool's foreground budget is 120s by default, so 90 leaves 30s of headroom for process start-up and lock contention while still covering a typical barrier. Rejected: raising the caller's Bash timeout to its 600000 ms maximum instead — that leaves zero headroom against a hard cap, and it fixes only callers who remember to pass it, whereas the default protects every caller by construction. Rejected: 110s — inside the budget but with too little margin to survive a slow claim.
- **The timeout contract already makes re-issuing correct**, so nothing else must change. Verified by running it: `claim <change> --as <label> --wait --timeout 3` against a never-completing barrier exited `0` after 3s with empty stdout and the stderr note `wait timed out after 3s (waiting on the current group/barrier).` A worker therefore loops on the same call, and `verified/build-task-coordination`'s "Wait times out empty" scenario keeps that behavior pinned.
- **Four sites name the default and must move together**: `claim_task.sh:51` (the header comment), `claim_task.sh:103` (`TIMEOUT=600`, the value itself), `plugins/s/agents/sub-agent.md:93`, and `plugins/s/skills/build/SKILL.md:926`. The delta's own requirement text carries the fifth. A new test pins the value so the set cannot drift apart again — today no test asserts it, which is why 600 survived unexamined.
- **Turn-boundary rule.** `sub-agent.md`'s loop section gains a rule that a worker never ends its turn holding a claim: before stopping — including to wait on any long-running verification — it completes the task or releases it. The observed failure was a worker that wrote its file, started a background test run, and stopped with the task still `[~]`, which barriered every other builder. This is a distinct defect from backgrounding the claim, and the existing prose forbids only the latter.
- **Orchestrator stale check.** `build/SKILL.md`'s Phase 3 gains a step directing the orchestrator to run `claim_task.sh status <change> --stale-after <mins>` between fan-out rounds and to act on a `[stale]` line. Detection belongs to the orchestrator precisely because reclamation must stay manual.
- **Version bump.** Everything lands under `plugins/s/`, so `plugins/s/.claude-plugin/plugin.json` goes `0.6.207` to `0.6.208`.

Risk: 90s is shorter than some real barriers, so a worker may re-issue several times where it previously blocked once. That is the intended trade — a handful of cheap, foreground tool calls in place of one call the harness silently detaches — and the retry interval is unchanged, so no extra lock pressure results.
