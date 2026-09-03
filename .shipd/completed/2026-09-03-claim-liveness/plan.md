# claim-liveness
Status: verified

## Idea

Give the task coordinator claim liveness — holder-stamped, timestamped claims,
an in-shell blocking `claim --wait`, state-guarded `complete`/`release`, and a
stale-claim release — and ban background claim loops in the worker contract.

### Motivation

Two builds have hit the same pathology: sub-agents waiting at barriers invented
background shell poll loops whose claims outlived the agent's awareness,
leaving tasks `[~]`-held by nobody (twice in the workspace-universe-seam
build), and an unguarded `release <id>` even flipped a completed task back to
pending; the minute-cadence in-agent polling also multiplied full-context API
rounds (~610M cache-read tokens). The coordinator records no holder, no age,
and offers no way to wait.

### Details

- `claim` stamps each claim with a holder label and timestamp; `--as <label>`
  names the holder (defaulting to the session id).
- New `claim --wait [--timeout <secs>]`: the shell itself polls and blocks
  inside one invocation, so a waiting agent burns one tool call, not sixty.
- `complete`/`release` refuse a task that is not in-progress and verify the
  holder when both sides name one; both clear the claim record.
- `status` keeps its first line byte-identical and appends one
  `claimed:` line per in-progress task with holder, age, and a stale flag.
- New `release --stale <mins>` reclaims every claim older than the threshold.
- `plugins/s/agents/sub-agent.md` bans background claims and prescribes
  `claim --wait`; the build `SKILL.md` coordinator reference documents the new
  verbs.

Affected capabilities: `build-task-coordination` (modified:
`atomic-task-claiming-with-stable-ids`,
`completion-and-release-without-tracking-line-numbers`, `status-reporting`;
added: `stale-claim-reclamation`, `foreground-claim-discipline`). Impact:
`plugins/s/skills/build/scripts/claim_task.sh`,
`plugins/s/skills/build/tests/test_claim_task.py`,
`plugins/s/agents/sub-agent.md`, `plugins/s/skills/build/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (→ 0.6.172).

### Non-goals

- No change to orchestrator fan-out logic (already spec'd by
  `deterministic-fan-out-from-group-tags`) beyond the doc note that workers
  wait via `claim --wait`.
- No auto-reclaim inside `claim`: a stale claim is *flagged* and reclaimed
  only by an explicit `release --stale` — a slow-but-alive agent is never
  silently robbed of its task.
- No heartbeat/board integration for claims, and no change to task id
  semantics, group tags, readiness, or the branch guard.
- No Python rewrite: the coordinator stays a bash script.

## Implementation

- **Claim record storage.** A sidecar file
  `.shipd/planned/<change>/.tasks.claims`, TSV lines `id<TAB>holder<TAB>epoch`
  (epoch seconds via `date +%s`), read and rewritten only under the existing
  mkdir lock. `complete`/`release` delete the task's line; the file is removed
  when its last line goes. Rejected: stamping inside `tasks.md` — the
  checkbox grammar is load-bearing for the linter, `spec_status sync`, and
  ordinal ids, and must not change. Rejected: one file per claim — more
  cleanup surface for zero benefit at this scale.
- **Holder labels.** `--as <label>` on `claim`, `complete`, and `release`;
  default `${CLAUDE_CODE_SESSION_ID:-anon}`. Verification is *soft*: refuse
  (exit 1, naming both labels) only when the stored record carries a holder
  AND the caller passed `--as` with a different label — a bare
  `complete <change> <id>` keeps today's behavior, so every existing caller,
  test, and flow is unaffected. Rejected: hard verification — it would break
  the orchestrator's own takeover moves (this session's release-and-finish)
  and every existing script.
- **`claim --wait [--timeout <secs>]`** (default 600). Loop **without holding
  the lock**: attempt a normal claim (its own lock acquire/release), and on
  empty output sleep 5s and retry until the deadline. Exit contract mirrors
  today's single-shot claim: a win prints `ID<TAB>TEXT` (exit 0); "no pending
  tasks at all" returns immediately with the existing `No pending tasks.`
  stderr line (exit 0, empty stdout); a deadline hit prints
  `wait timed out after <secs>s (waiting on the current group/barrier).` to
  stderr (exit 0, empty stdout). Refactor the claim critical section into a
  `claim_once` function that acquires and releases the lock itself (explicit
  `rmdir` + trap reset per iteration), so repeated attempts never deadlock on
  the EXIT trap. Rejected: exiting non-zero on timeout — empty-stdout-exit-0
  is the established "nothing claimed" contract and agents branch on stdout.
- **State guards.** `complete` refuses (exit 1, naming the current state) a
  task whose box is not `[~]`; `release` likewise refuses a `[ ]` or `[x]`
  task. This makes the observed `[x]`→`[ ]` flip impossible. No `--force`:
  the recovery for a genuinely wedged mark is `release --stale` or editing
  `tasks.md` by hand, both deliberate acts.
- **`status` output.** First line stays byte-identical
  (`pending=… in_progress=… done=…`). After it, one line per in-progress
  task: `claimed: <id> by <holder> age <Nm|Ns|Nh Nm>` with ` [stale]`
  appended when age exceeds the threshold (default 30 minutes,
  `--stale-after <mins>` overrides). A `[~]` task with no claim record (a
  pre-change file, or a hand-edit) prints `by unknown age unknown [stale]` —
  visible, never fatal.
- **`release --stale <mins>`.** Under the lock: release every `[~]` task
  whose record epoch is older than the threshold — records missing entirely
  count as stale — printing one `Task <id> released (held by <holder> for
  <age>).` line each, `No stale claims.` when none. Mutually exclusive with
  an explicit id.
- **Worker/orchestrator docs.** `sub-agent.md` "Your loop" step 2: wait for a
  barrier with `claim --wait` in the foreground; **never** run claim/status
  poll loops as background processes (a detached claim outlives your
  awareness of it); pass a stable personal `--as` label — the spawn
  description's role (e.g. `builder 2`) or a short label invented once and
  reused. Build `SKILL.md`'s coordinator reference gains the new
  verbs/flags verbatim.
- **Tests** (`test_claim_task.py`, stdlib-only): holder stamping and record
  cleanup; soft verification (mismatch refused, bare call allowed);
  `--wait` winning immediately, timing out fast (`--timeout 1`), and
  returning at once when nothing is pending; barrier-released mid-wait claim
  (background writer completes the barrier task); status first-line
  byte-identity plus `claimed:` lines and the stale flag (records back-dated
  by rewriting the sidecar's epoch); complete/release state-guard refusals
  including the archived flip regression; `release --stale` reclaiming old
  and record-less claims while sparing fresh ones; existing suites unchanged.
- Runnable premise (observed this session): `release workspace-universe-seam
  16` on a completed task printed `Task 16 released.` and set the box back to
  `[ ]` (coordinator status went `done=18` → `done=17`) — the guard this
  plan adds.
- Risk: `date +%s` and `sleep` granularity differ across platforms; ages are
  displayed coarsely (minutes) and thresholds compared in seconds, so drift
  of a few seconds is harmless.
