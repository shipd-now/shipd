## ADDED Requirements

### Requirement: Run without a PR enters repo mode
id: room-run-repo-mode

`room.py run` SHALL accept the `pr` positional as optional. When it is given, the run SHALL behave exactly as before, with `--since` defaulting to `0:0` and `--budget` to `14400`. When it is omitted, the run SHALL enter repo mode. If `--repo` is absent, `--role` is `author`, `--since` is given, or `--request-review` is given, then repo mode SHALL exit `2` as a usage error before any GitHub call. If `--state` is given with a PR, then the run SHALL exit `2` the same way. Repo mode SHALL read the acting login once (`gh api user`) and SHALL exit `1` with one `Error:` line when the login cannot be read. It SHALL then run the harness preflight exactly as the per-PR run does, exiting `1` on failure, and SHALL set `SHIPD_ROOM_AGENT` to the agent name. The preflight runs before any state file is opened.

#### Scenario: Repo mode needs a repository
- **WHEN** `run --role reviewer --agent rev-b` runs with no PR and no `--repo`
- **THEN** the exit code is `2` and no `gh` call is made

#### Scenario: Repo mode refuses the author role
- **WHEN** `run --repo o/r --role author --agent a` runs
- **THEN** the exit code is `2` and no `gh` call is made

#### Scenario: The per-PR form is unchanged
- **WHEN** `run 7 --role reviewer --agent rev-b` runs on a merged PR
- **THEN** the summary's `reason` is `closed`, as before this change

### Requirement: Repo mode answers each PR that asks for the agent
id: room-run-repo-poll

Each poll, repo mode SHALL list the open pull requests with `gh pr list --repo <R> --state open --json number,url,author,updatedAt --limit 100` and SHALL visit them in ascending number. It SHALL skip a PR whose author login is empty or equals the acting login ignoring case, warning once per PR on stderr, and SHALL never join, read, or post on it. It SHALL also skip a PR parked earlier in this process, and a PR whose `updatedAt` equals the value seen on its last visit when that visit surfaced no task. For every other PR it SHALL run `watch`'s own logic once, with `once` set and from that PR's cursor, capturing stdout. When task lines surface, it SHALL first post or refresh its card through `join`'s logic once per PR per process, with the run's role, harness, description, and skills. It SHALL then call the turn runner once with the prompt `/s:room <url> role <role>, skills <s1>, ...`, the run's root as working directory, and that PR's own stored session id as resume id (`None` the first time). After the turn it SHALL store the returned session id, advance the PR's cursor to the last surfaced line's `cursor`, and continue with the next PR. Only one turn SHALL run at a time. Between polls it SHALL sleep `--interval` seconds, and an idle poll SHALL call no turn runner.

#### Scenario: Two PRs each get their own session
- **WHEN** open PRs 7 and 9 each hold a task to `rev-b`, and the fake runner returns `s-7` for PR 7's turn and `s-9` for PR 9's
- **THEN** the runner is called once per PR with resume id `None`, each prompt names its own PR URL, and a later task on PR 7 resumes `s-7`

#### Scenario: A PR authored by the acting login is skipped
- **WHEN** the acting login is `rev-b-login` and open PR 7, authored by `REV-B-LOGIN`, holds a task to `rev-b`
- **THEN** nothing is posted on PR 7, the runner is never called, and stderr names PR 7 once

#### Scenario: A PR without a task for the agent costs no turn
- **WHEN** the only open PR holds a task addressed to another agent
- **THEN** the runner is never called and no card is posted

#### Scenario: An unchanged PR is not re-read
- **WHEN** two polls see PR 7 with the same `updatedAt` and no task
- **THEN** PR 7's comments are read only once

### Requirement: Repo mode keeps a locked per-PR state file
id: room-run-repo-state

Repo mode SHALL keep each PR's cursor and session id in a JSON state file, at `--state` when given, else at `~/.shipd/room-run/<owner>/<name>/<agent>.json`. The file SHALL hold `{"version": 1, "repo", "agent", "prs": {"<number>": {"cursor": "<issue>:<review>", "session_id"}}}`. It SHALL be read at start, so a restarted run resumes each PR's session from its stored cursor. It SHALL be written atomically, through a temporary file and a rename, after every turn and whenever a PR that has left the open list is pruned. If the file is unreadable or malformed, then the run SHALL warn once and start with no entries. Repo mode SHALL hold an exclusive non-blocking `flock` on `<state>.lock` for its lifetime. If another process holds that lock, then it SHALL print one `Error:` line naming the state path and exit `1` having posted nothing.

#### Scenario: A restart resumes from the stored cursor and session
- **WHEN** a state file stores PR 7 with cursor `1005:0` and session `s-7`, and PR 7's only task to the agent was last commented at id `1003`
- **THEN** the runner is never called; and when a new task comment `1010` arrives, the turn resumes `s-7`

#### Scenario: A closed PR is pruned
- **WHEN** the state file stores PR 5 and PR 5 is not in the open list
- **THEN** the written state file holds no entry for PR 5

#### Scenario: A second runner is refused
- **WHEN** the lock on the state file is already held
- **THEN** stderr holds one `Error:` line naming the state path, the exit code is `1`, and nothing is posted

### Requirement: Repo mode stops cleanly and survives failures
id: room-run-repo-stop

If a turn returns not ok, then repo mode SHALL warn on stderr naming the PR and the failure, park that PR for the rest of the process, and run the preflight again. If that preflight fails, then the run SHALL stop with reason `preflight-failed`. `--max-turns` (default `10`) SHALL count turns per PR per process, parking the PR once it is reached. `--budget` SHALL have no limit by default in repo mode; when given, the run SHALL stop with reason `budget` once that many seconds have elapsed on the injectable clock. If a list or watch call raises a room error whose text contains `rate limit` (ignoring case), then the run SHALL warn and sleep a backoff that starts at twice `--interval` and doubles up to `900` seconds, resetting after the next successful list. Any other list or watch error SHALL warn and be retried on the next poll. A `KeyboardInterrupt` SHALL stop the run with reason `interrupted`. On stopping, the run SHALL save the state file and print one stdout line `json.dumps` of `{"mode": "repo", "repo", "turns", "reason", "prs"}`, where `prs` maps each PR number visited this process to its `turns`, `session_id`, and `cursor`, plus `failure` for `preflight-failed`. It SHALL exit `0` for `budget`, `130` for `interrupted`, and `1` with one `Error:` line naming the harness sign-in command for `preflight-failed`. Stdout SHALL carry nothing else.

#### Scenario: A failed turn parks only its PR
- **WHEN** PR 7's turn fails, the preflight still passes, and PR 9 holds a task
- **THEN** PR 9's turn runs, PR 7 gets no second turn in this process, and the run keeps polling

#### Scenario: An expired sign-in stops the run
- **WHEN** a turn fails and the follow-up preflight returns not ok
- **THEN** the summary's `reason` is `preflight-failed`, stderr holds one `Error:` line containing `claude auth login`, and the exit code is `1`

#### Scenario: A rate limit backs off
- **WHEN** the PR list fails with `API rate limit exceeded` under `--interval 30`
- **THEN** the next sleep is `60` seconds, and a following failure sleeps `120`

#### Scenario: Ctrl-C prints the summary
- **WHEN** the fake sleep raises `KeyboardInterrupt` after one turn
- **THEN** stdout is one line whose `mode` is `repo` and `reason` is `interrupted`, the state file holds the turn's cursor, and the exit code is `130`

### Requirement: Repo mode tests, docs, and version
id: room-run-repo-docs

Repo mode SHALL be covered offline in `plugins/s/skills/room/tests/test_room_run_repo.py` through `room.main` with a multi-PR fake `gh`, a fake runner, a fake preflight, a fake clock and sleep, and a temporary `--state`. The existing room suite SHALL stay green. `docs/room-run.md` SHALL stay a lint-clean how-to that shows `shipd room run --repo` with no PR number for the reviewer, the state file, Ctrl-C, and the repo-mode limits. `plugin.json` SHALL carry a version one patch above `main`'s.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests` runs
- **THEN** it reports `OK`

#### Scenario: The how-to lints clean and shows repo mode
- **WHEN** `docs_lint.py docs/room-run.md` runs
- **THEN** it exits `0` and the doc contains `shipd room run --repo` and `--state`
