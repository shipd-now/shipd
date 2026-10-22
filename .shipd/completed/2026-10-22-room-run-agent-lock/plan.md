# room-run-agent-lock
Status: verified
Planned-at: eab22422a85ed93b807fa7c870a23e2309a03666
Gated-hash: 292444881b07

## Idea

Lock `shipd room run` per repository and agent, so two runners for the same
agent can never answer the same pull request at once.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/39 two reviewer-b
runners were alive. A stale one ran with its own `--state` file, so the
state-file lock never saw the other runner. Both re-reviewed the same head:
the stale one approved, auto-merge fired, and the real one's
`CHANGES_REQUESTED` landed one second after the merge. Real findings reached
`main` unfixed.

### Details

- Repo mode takes an exclusive lock on the agent lock,
  `~/.shipd/room-run/<owner>/<name>/<agent>.json.lock`, whatever `--state`
  says. It keeps the existing `<state>.lock` too.
- PR mode takes a shared lock on the same agent lock and an exclusive lock on
  `<agent>.pr-<N>.lock` beside it.
- A repo-wide runner therefore refuses to start beside any runner of the same
  agent, and the reverse. Two PR runners of one agent on one PR refuse each
  other. PR runners on different PRs still run side by side.
- A refused runner prints one `Error:` line naming the agent, the repository
  and the lock path, posts nothing, and exits `1`.
- `plugin.json` goes from `0.6.343` to `0.6.344`.

Affected capabilities: `room-runner` (added `room-run-agent-lock`). Impact:
`plugins/s/skills/room/scripts/room_run_repo.py`,
`plugins/s/skills/room/scripts/room_run.py`,
`plugins/s/skills/room/tests/test_room_run_repo.py`,
`plugins/s/skills/room/tests/test_room_run.py`, `docs/room-run.md`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No lock across machines or accounts. The lock is a local `flock`.
- No PID file or stale-lock cleanup. `flock` releases when the process dies.
- No change to the state file's format or its location.

## Implementation

- **Lock helper.** In `room_run_repo.py`, replace `lock_state(path)` with
  `hold_lock(path, refusal, shared=False)`. It creates the directory, opens
  `path` for append, and takes `LOCK_SH` or `LOCK_EX` with `LOCK_NB`. On
  `BlockingIOError` it closes the handle and raises
  `room.RoomError(refusal)`. It returns the open handle.
- **Agent lock path.** Add `agent_lock_path(repo, agent)`, returning
  `default_state_path(repo, agent) + ".lock"`, and
  `pr_lock_path(repo, agent, number)`, returning the same directory joined
  with `<agent>.pr-<number>.lock` (agent `/` replaced by `_`, as in
  `default_state_path`).
- **Refusal text.** One shared format:
  `"another room run already serves agent %s on %s (lock %s); stop it first"`
  with agent, repo and the lock path.
- **Repo mode.** In `cmd_run_repo`, take the exclusive agent lock first. When
  the state path's lock differs from the agent lock, also take the exclusive
  `<state>.lock` with the existing text
  `"another room run holds %s" % path`. Release both in the `finally`.
- **PR mode.** Add `lock_pr_run(repo, agent, number)` to `room_run_repo.py`.
  It takes the shared agent lock, then the exclusive PR lock, closing the
  first if the second is refused, and returns both handles. In
  `room_run.cmd_run`, call it right after the harness preflight passes and
  before `gh pr view`, so a refused run has joined and posted nothing. Move
  the body after that point into `_run_pr(...)`, and wrap the call in
  `try/finally` that closes both handles.
- **Tests.** The test harness `_run` points `HOME` at a fresh temp directory,
  so locks land there. A contention test passes its own `env={"HOME": h}`,
  holds the lock with `fcntl.flock` on the path under `h`, and runs the verb.

Risk: a runner that hangs keeps its lock, so a restart is refused until the
hung process is stopped. That is the intended guard.

## Questions and answers

### Q1: Lock on the state path, or on the repository and agent?
- **Question:** Options: (1) lock on the repository and agent, with PR runs
  taking a shared agent lock plus an exclusive per-PR lock; (2) keep the
  state-path lock only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, settled in the session after the PR 39 race.

## Readiness attestation

### Problem and motivation

Two runners of one agent can run at once when their `--state` paths differ.

Evidence:

- `plugins/s/skills/room/scripts/room_run_repo.py:196-197` locks
  `opts.state or default_state_path(...)`, so a custom `--state` gets its own
  lock.
- `plugins/s/skills/room/scripts/room_run.py:259-345`: PR mode takes no lock.
- The PR 39 race: a stray runner with a scratch `--state` approved one second
  before the real runner's change request.

### Scope and non-goals

Two scripts, two test files, one doc and the version change.

Evidence:

- In scope: `room_run_repo.py` `lock_state` and `cmd_run_repo`,
  `room_run.py` `cmd_run`.
- Out of scope: the state file format, `room.py`, the wake bundle.

### Affected capabilities and files

One capability, `room-runner`, gains `room-run-agent-lock`. The existing
`room-run-repo-state` lock stays true unchanged.

Evidence:

- Files: listed under Details.
- `plugin.json` is `0.6.343` on `origin/main`.

### No open task-shaping decision

The lock design is settled by Q1.

Evidence:

- Q1, answered by the user.
