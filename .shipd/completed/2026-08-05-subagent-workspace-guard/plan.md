# subagent-workspace-guard
Status: verified

## Idea

Stop a builder from working in the wrong checkout: the claim script refuses
mutating verbs from a checkout that is not the change's branch, and the
sub-agent contract gains a binding workspace gate it must pass before its
first claim or edit.

### Motivation

A builder just implemented a change correctly but edited the **main
checkout** instead of its named worktree — caught only by the orchestrator's
independent verification, because nothing mechanical or contractual pins a
sub-agent to its worktree; the claim script hands out tasks from any
directory and `agents/sub-agent.md` never mentions worktrees or branches.

### Details

- `claim_task.sh` `claim`/`complete`/`release` refuse (exit non-zero, naming
  both branches) when the repo has a `change/<change>` branch and the
  current checkout is not on it; `status`/`next` stay read-only-unguarded.
  Repos with no `change/<change>` branch (onboarding sandboxes, eval
  scratch repos, non-git fixture dirs) are unaffected.
- `agents/sub-agent.md` gains a workspace gate: before the first claim or
  file edit, verify the working directory is the named worktree root and
  `git rev-parse --abbrev-ref HEAD` prints `change/<change>`; on mismatch,
  stop and report instead of proceeding; every edit uses paths inside the
  worktree root, never absolute paths into another checkout.

Affected capabilities: `build-task-coordination` (added requirement),
`build-subagent-handoff` (added requirement). Impact:
`plugins/s/skills/build/scripts/claim_task.sh`,
`plugins/s/agents/sub-agent.md`,
`plugins/s/skills/build/tests/test_claim_task.py`, a new
`plugins/s/skills/build/tests/test_subagent_contract.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No guard on the validator contract (it writes throwaway probes, not the
  change's files) and no orchestrator-side changes.
- No cwd-based heuristics beyond the branch check — the branch is the
  identity the worktree flow already guarantees.
- No env-var escape hatch: a repo without the change branch never triggers
  the guard, which already covers every sanctioned non-worktree flow.

## Implementation

- **Guard placement.** A `require_change_branch()` function in
  `claim_task.sh`, called by `claim`, `complete`, and `release` before any
  lock/edit. Logic: if `git rev-parse --verify --quiet
  refs/heads/change/<change>` succeeds (the branch exists in this repo) and
  `git branch --show-current` prints anything other than
  `change/<change>`, print
  `refusing: current branch '<cur>' is not 'change/<change>' — run from the
  change's worktree` to stderr and exit 3. Outside a git checkout (or on
  the right branch, or with no such branch) the verbs behave exactly as
  today. Rejected: guarding `status`/`next` — read-only verbs are used from
  the main checkout legitimately (the board, the orchestrator).
- **Exit code 3** distinguishes the guard from the existing usage/contention
  exits so callers can special-case it.
- **Contract gate.** A `## Workspace gate (before any claim or edit)`
  section near the top of `agents/sub-agent.md`: confirm cwd is the spawn
  message's worktree root; run `git rev-parse --abbrev-ref HEAD` and require
  `change/<change>`; on mismatch stop and report the mismatch as the final
  message (do not claim, do not edit, do not cd elsewhere); all file paths
  in edits and commands stay inside the worktree root.
- **Contract test.** `tests/test_subagent_contract.py` (stdlib) asserts
  `agents/sub-agent.md` contains the gate section heading, the
  `git rev-parse --abbrev-ref HEAD` check, and the stop-on-mismatch
  instruction — pinning the contract file to the requirement the way the
  statusline's behavior is pinned by `test_statusline.py`.
- **Risk**: `git branch --show-current` prints empty on detached HEAD; the
  guard treats empty as a mismatch (a detached checkout is not the change
  branch) — covered by a test.
