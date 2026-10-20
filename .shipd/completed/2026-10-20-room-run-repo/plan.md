# room-run-repo
Status: verified
Planned-at: 7656ed263dde0e57a29da305a35730337ee0e92c
Gated-hash: d12930436402

## Idea

Add a repo-wide reviewer mode to `shipd room run`, plus two small fixes: the gate resolves only threads it opened, and the copilot report names `shipd copilot update`.

### Motivation

A reviewer on their own laptop must start `shipd room run <pr>` by hand for every pull request, so no one long-running process can answer every PR that asks for them. Separately, the gate's `resolve-threads` job can silently resolve another Actions workflow's threads, and the bare `shipd copilot` report points stale files at `add` / `add --room` instead of `update`.

### Details

- `shipd room run --repo R --role reviewer|ci --agent NAME` with no PR: polls open PRs with no token spend, runs one resumed `/s:room` turn per PR holding a task addressed to the agent, keeps a per-PR cursor and session in a local state file, and runs until Ctrl-C.
- Gate inline comments carry a hidden `<!-- shipd-gate-finding -->` line; `resolve-threads` requires it.
- `copilot_states` / `room_wake_states` stale details say `shipd copilot update`.

Affected capabilities: `room-runner`, `copilot-review-skill` (modified), `shipd-cli`. Impact: `plugins/s/skills/room/scripts/{room.py,room_run.py,room_run_repo.py}`, room tests, `docs/room-run.md`, `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/bin/shipd`, `test_copilot_verb.py`, `plugin.json`.

### Non-goals

- No author repo mode; no GitHub review request as a trigger; no concurrent turns.
- No auto-resolve of gate threads posted before the marker existed.
- The per-PR `run <pr>` form is unchanged.

## Implementation

- **Shape.** `run`'s `pr` becomes `nargs="?"`; `room_run.cmd_run` hands `opts.pr is None` to a new `room_run_repo.cmd_run_repo(opts, parser, gh, runner, sleep, clock, preflight)` (lazy import; the Actions wake bundles only `room.py`). `--since` and `--budget` defaults become `None`, resolved to `(0, 0)` and `14400` on the per-PR path. New `--state PATH` (repo mode only).
- **Scheduler (serial).** Each poll: `gh pr list --repo R --state open --json number,url,author,updatedAt --limit 100`. Skip parked PRs, PRs whose author equals the login (warn once), and PRs whose `updatedAt` equals the last one seen with nothing surfaced. For the rest, run `room.cmd_watch` with `once=True` and the PR's cursor, stdout captured. On task lines: join once per process via `cmd_join`, run one turn with that PR's session id, save the cursor and session, then go on. Rejected: threads, because `cmd_watch`/`cmd_join` redirect process-global stdout and set `os.environ`.
- **Discovery.** Room tasks only, via `is_actionable` (before a join, only tasks addressed to the agent).
- **State.** JSON `{"version": 1, "repo", "agent", "prs": {"<n>": {"cursor": "i:r", "session_id"}}}` at `~/.shipd/room-run/<owner>/<name>/<agent>.json`. Written atomically (temp file plus `os.replace`) after each turn, pruned to the open list, and an unreadable file warns and starts empty. `fcntl.flock` on `<state>.lock` (non-blocking) refuses a second runner.
- **Failure and bounds.** A failed turn parks the PR and re-runs the preflight; a failed preflight stops the run (`preflight-failed`, exit 1). `--max-turns` is per PR per process and parks the PR. `--budget` has no limit by default. A `RoomError` naming a rate limit backs off, doubling from `2*interval` up to 900 s and resetting on a clean list; other list or watch errors warn and retry next poll.
- **Gate marker.** `inline_body` ends with the marker line. The thread query adds `body`, and the selector also requires the first comment's last non-blank line to equal the marker. Room parsing ignores it, because its regex matches only `shipd-room` markers.

Risk: does a comment bump `updatedAt`? Observed yes (see attestation). A missed bump only delays a task until the PR's next update.

## Questions and answers

### Q1: CLI shape of repo mode
- **Question:** Select repo mode by (1) omitting the PR, with `--repo` required; (2) an `--all-prs` flag; (3) a new verb `serve`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) omit the PR; `--repo` is required in repo mode.
- **Queued:** q-room-run-repo-cli-shape

### Q2: Does a review request count
- **Question:** Does a review request for the acting login with no room task count? (1) no, room tasks only; (2) yes, one turn with a synthetic review prompt. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) room tasks only.
- **Queued:** q-room-run-repo-review-request-counts

### Q3: Turn concurrency
- **Question:** Run turns (1) serially, one at a time; (2) through a bounded worker pool with `--max-concurrent`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) serial.
- **Queued:** q-room-run-repo-turn-concurrency

### Q4: Where the cursor and session live
- **Question:** (1) a locked local JSON state file per repo and agent, `--state` override; (2) memory only; (3) the card metadata. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) a local state file.
- **Queued:** q-room-run-repo-state-store

### Q5: Author repo mode
- **Question:** (1) repo mode takes reviewer and ci only, and author is exit 2; (2) also add an author repo mode. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) reviewer and ci only.
- **Queued:** none

### Q6: Gate threads posted before the marker
- **Question:** (1) marker only, so a person resolves older threads once; (2) also match the legacy severity heading. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) marker only.
- **Queued:** q-gate-finding-marker-legacy-threads

### Q7: Failed turn, turn cap, budget in repo mode
- **Question:** (1) park the PR, re-run the preflight, and stop only if it fails; `--max-turns` per PR parks it; no budget by default; (2) stop on any failed turn; (3) retry next poll. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1).
- **Queued:** none

## Readiness attestation

### Problem and motivation

A reviewer cannot keep one runner going for a whole repository. The gate's thread selection and the copilot report hint are wrong.

Evidence:

- `room.py:1080` makes `pr` a required positional; `room_run.py` `cmd_run` loops one PR until it closes.
- `copilot-review-gate.yml:1468` `GATE = ("github-actions", "github-actions[bot]")` matches by author only.
- `bin/shipd:2100,2113,2149,2163` stale details name `add` / `add --room`.

### Scope and non-goals

Reviewer and ci repo mode, the gate marker, and the hint; the per-PR form and author mode stay as they are.

Evidence:

- Capability `room-runner` requirements `room-run-start` through `room-run-ci-findings` stay as written.
- `copilot-update` (shipd-cli) already refreshes stale gate and wake sets.

### Affected capabilities and files

Three capabilities, about ten files.

Evidence:

- `room-runner` (added), `copilot-review-skill` `gate-resolves-superseded-threads` (base 57cd8a5b7c8c), `shipd-cli` (added).
- Files: `room.py:1077-1121,1123-1140`, `room_run.py:cmd_run`, `copilot-review-gate.yml:1164-1174,1425-1485`, `bin/shipd:2095-2165`, `test_copilot_verb.py:1746`, `test_room.py` `FakeGh`.
- Runnable premise: `room.py run --role reviewer --repo o/r` → exit 2, "the following arguments are required: pr".
- Runnable premise: `gh pr list --repo shipd-now/shipd --state open --json number,url,author,updatedAt` → exit 0, `author.login` and `updatedAt` present; PR 250's `updatedAt` equals its last issue comment's `created_at`.
- Room marker regex `room_schema.py:55` matches only `shipd-room` / `shipd-room-card`.

### No open task-shaping decision

Seven decisions were found; the oracle answered INSUFFICIENT on each, and each takes the PLANNER default, Q1 to Q7.

Evidence:

- CLI shape Q1, triggers Q2, concurrency Q3, state Q4, author mode Q5, legacy threads Q6, failure policy Q7.
- Personal memory store: absent, so skipped.
