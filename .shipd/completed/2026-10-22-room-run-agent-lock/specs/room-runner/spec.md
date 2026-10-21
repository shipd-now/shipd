## ADDED Requirements

### Requirement: One runner per repository and agent
id: room-run-agent-lock

`room run` SHALL lock on the repository and agent, not only on the state
file. Repo mode SHALL hold an exclusive non-blocking `flock` on
`~/.shipd/room-run/<owner>/<name>/<agent>.json.lock`, with the repository
lowercased, for its lifetime, whatever `--state` names. When `<state>.lock` is
another file, repo mode SHALL hold it too. PR mode SHALL hold a shared non-blocking `flock` on
that same file and an exclusive non-blocking `flock` on
`<agent>.pr-<number>.lock` in the same directory, both taken after the harness
preflight and before the run joins the room. If either lock is held, then the
run SHALL print one `Error:` line naming the agent, the repository and the
lock path, SHALL post nothing, SHALL call no runner, and SHALL exit `1`. PR
runs of one agent on different PRs SHALL NOT refuse each other.

#### Scenario: A repo runner with a custom state file is refused
- **WHEN** another process holds the agent lock of `rev-b` on `o/r` and repo
  mode starts with `--state` pointing elsewhere
- **THEN** stderr holds one `Error:` line naming `rev-b`, `o/r` and the lock
  path, nothing is posted, the runner is never called, and the exit code is
  `1`

#### Scenario: A PR run is refused while a repo runner holds the agent
- **WHEN** another process holds the exclusive agent lock of `rev-b` on `o/r`
  and `room run 7 --role reviewer --agent rev-b` starts
- **THEN** the run exits `1` with one `Error:` line, before joining the room

#### Scenario: Two PR runs on one PR refuse each other
- **WHEN** another process holds the PR 7 lock of `rev-b` on `o/r`
- **THEN** a PR run of `rev-b` on PR 7 exits `1` with one `Error:` line

#### Scenario: PR runs on different PRs coexist
- **WHEN** another process holds the PR 8 lock of `rev-b` on `o/r`
- **THEN** a PR run of `rev-b` on PR 7 starts normally
