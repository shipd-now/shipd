# room-runner

### Requirement: Run starts on a checked account and joins once
id: room-run-start

`room.py run <pr> --role author|reviewer|ci [--skill S]... [--description D]
[--harness H] [--model M] [--max-turns N] [--budget S] [--turn-timeout S]
[--interval S] [--since CURSOR]` SHALL resolve the agent, the root, and the
room exactly as the other verbs do, and SHALL reject an unknown `--harness`
(checked with `session_driver.runner_for`) and a missing `--role` as usage
errors (exit `2`). Before posting anything it SHALL read the acting login
(`gh api user`) and the PR author (`gh pr view --json author`). If the login
cannot be read, then it SHALL print one `Error:` line and exit `1`. If the
role is `reviewer` or `ci` and the author cannot be read or equals the login
case-insensitively, then it SHALL print `whoami`'s `Error:` line and exit `1`
having posted nothing. Where the role is `author` and the login differs from
the PR author, it SHALL warn on stderr and continue. It SHALL then post or
refresh its card once through `join`'s logic, with the given role, harness,
description, and skills — `review-finding`, `question`, `status` when no
`--skill` is given. It SHALL pass no `env` override to any subprocess, so
`GH_TOKEN` or `GH_CONFIG_DIR` in the process environment reaches both the `gh`
calls and the spawned session.

#### Scenario: A reviewer on the author's account is refused
- **WHEN** `run 7 --role reviewer` runs with login `Mikkel` on a PR authored by
  `mikkel`
- **THEN** one `Error:` line is printed, the exit code is `1`, no comment is
  posted, and the turn runner is never called

#### Scenario: The card is joined once with the run's role and skills
- **WHEN** `run 7 --role reviewer --agent rev-b` runs on a PR authored by
  `mikkel` with login `reviewer-b` and the PR is already merged
- **THEN** exactly one card is posted, carrying role `reviewer`, and skills
  `review-finding`, `question`, `status`

#### Scenario: An unknown harness is a usage error
- **WHEN** `run 7 --role author --harness nope` runs
- **THEN** the exit code is `2` and nothing is read from or posted to GitHub

### Requirement: Run loops watch and one resumed turn per task
id: room-run-loop

The run SHALL loop: run `watch`'s own logic (`cmd_watch`) from the current
cursor (initially `--since`, default `0:0`) with `--interval` and a timeout of
the wall-clock budget still remaining, capturing its stdout. When it surfaces
one or more task lines (and no `closed` line), the run SHALL call the turn
runner once with the prompt `/s:room <url> role <role>, skills <s1>, <s2>...`,
where `<url>` is the PR's `url` from `gh pr view --json url`, the working
directory is the run's root, and the resume id is the session id of the
previous turn (`None` on the first). Before the first turn it SHALL set
`SHIPD_ROOM_AGENT` to the agent name in its own environment. After the turn it
SHALL set the cursor to the last surfaced line's `cursor` and watch again. The
default runner SHALL call `session_driver.run_turn` with the harness, `--model`
as `effort`, the config's `model` as `model_base`, `--turn-timeout`, and the
plugin root as `plugin_dir`. The run SHALL print nothing on stdout except its
final summary line.

#### Scenario: Two tasks resume one session
- **WHEN** a task to the agent is waiting, the fake runner answers it and
  returns session `s-1`, and the other agent then opens a second task
- **THEN** the runner is called twice, the first with resume id `None` and the
  second with `s-1`, both prompts start `/s:room https://github.com/o/r/pull/7
  role author`, and the summary's `turns` is `2`

#### Scenario: The agent name reaches the session
- **WHEN** the run is started with `--agent rev-b` and the fake runner reads
  `SHIPD_ROOM_AGENT`
- **THEN** it reads `rev-b`

#### Scenario: No task spends no turn
- **WHEN** no task is ever actionable and the budget elapses on the fake clock
- **THEN** the runner is never called and the summary's `turns` is `0`

### Requirement: Run stops on close, cap, budget, or failure with one summary
id: room-run-stop

The run SHALL stop when `watch` prints a `closed` line (reason `closed`,
taking no turn even when that poll surfaced a task), after the `--max-turns`th
turn (reason `turn-cap`, default `10`), when the `--budget` seconds (default
`14400`) have elapsed on the injectable clock or a watch ends with no task
(reason `budget`), when a turn returns not ok (reason `turn-failed`), or when
the watch raises a room error (reason `watch-failed`). It SHALL then print one
stdout line `json.dumps` of `{"turns", "session_id", "reason", "context",
"cursor"}`, plus `closed` (`merged` or `closed`) for reason `closed` and
`failure` for the two failure reasons. It SHALL exit `0` for `closed`,
`turn-cap`, and `budget`, and for `turn-failed` and `watch-failed` SHALL also
print one `Error:` line on stderr and exit `1`.

#### Scenario: A merged PR ends the run
- **WHEN** the fake PR is `MERGED` when the run first watches
- **THEN** stdout is one line whose `reason` is `closed` and `closed` is
  `merged`, and the exit code is `0`

#### Scenario: The turn cap ends the run
- **WHEN** `--max-turns 1` is given and a task is waiting
- **THEN** the runner is called once and the summary's `reason` is `turn-cap`

#### Scenario: A failed turn ends the run
- **WHEN** the fake runner returns `(False, "session CLI exited 1: boom",
  None)`
- **THEN** the summary's `reason` is `turn-failed` with that `failure`, stderr
  holds one `Error:` line, and the exit code is `1`

### Requirement: Run tests, banner, docs, and version
id: room-run-tests-docs

The run SHALL be covered in `plugins/s/skills/room/tests/test_room_run.py`
through `room.main(argv, gh=FakeGh(...), sleep=..., clock=..., runner=...)`
with no network and no real session. The `shipd` banner's `room` line SHALL
name `run`. `docs/room-run.md` SHALL be a lint-clean how-to showing the
two-terminal setup — the author in the PR worktree on the default login, the
reviewer with `GH_CONFIG_DIR=~/.config/gh-reviewer` — and SHALL be linked from
`docs/pr-room.md`; `docs/room-wake-reference.md`'s "Replies wake no other
workflow" limit SHALL point at `shipd room run`. `plugin.json` SHALL carry a
version one patch above `main`'s.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests` runs
- **THEN** it reports `OK`

#### Scenario: The how-to lints clean and is linked
- **WHEN** `docs_lint.py docs/room-run.md` runs
- **THEN** it exits `0`, `docs/pr-room.md` links `room-run.md`, and
  `docs/room-wake-reference.md` names `shipd room run`

### Requirement: Run preflights the harness sign-in before joining
id: room-run-preflight

`session_driver` SHALL expose `preflight(cwd, harness=DEFAULT_HARNESS,
binary=None, effort=None, model_base=None, timeout=PREFLIGHT_TIMEOUT)`
returning `(ok, failure)`: it SHALL run one headless turn of `harness` with
the fixed `PREFLIGHT_PROMPT`, no resume id, no plugin dir, and a 120-second
default timeout, through the same runner record a real turn uses. Every
`RUNNERS` record SHALL carry a `login` string naming the harness's sign-in
command (`claude auth login`, `opencode auth login`), returned by
`login_hint(harness)`. After its identity check and before it posts its card,
`room.py run` SHALL call its preflight seam (`main`'s `preflight` keyword,
default `session_driver.preflight` with the run's harness, `--model`, and the
config's `model`). If the preflight returns not ok, then the run SHALL print
one `Error:` line naming the harness, the failure, and its `login` hint, SHALL
print nothing on stdout, SHALL post nothing, SHALL never call the turn runner,
and SHALL exit `1`.

#### Scenario: An expired sign-in stops the run before join
- **WHEN** `run 7 --role reviewer` runs with a fake preflight returning
  `(False, "session CLI exited 1: Failed to authenticate: OAuth session
  expired")`
- **THEN** stderr holds one `Error:` line containing `claude auth login`,
  stdout is empty, no comment is posted, the runner is never called, and the
  exit code is `1`

#### Scenario: The probe uses the runner's argv without plugin or resume
- **WHEN** `preflight` runs with a fake `claude` binary that records its
  arguments and exits `0`
- **THEN** it returns `(True, None)` and the recorded arguments carry `-p`
  and `PREFLIGHT_PROMPT` and neither `--plugin-dir` nor `--resume`

#### Scenario: A failing probe reports the CLI's reason
- **WHEN** `preflight` runs with a fake binary that prints `{"result":
  "Failed to authenticate"}` and exits `1`
- **THEN** it returns `ok` False with a failure containing
  `Failed to authenticate`

#### Scenario: Every runner names its sign-in command
- **WHEN** `login_hint` is read for every key of `RUNNERS`
- **THEN** each returns a non-empty string, and `claude`'s is
  `claude auth login`

### Requirement: An author run requests the first review
id: room-run-request-review

`room.py run` SHALL accept a repeatable `--request-review AGENT`. If it is
given with a `--role` other than `author`, or names the run's own agent, then
the run SHALL exit `2` as a usage error before any GitHub call. After joining,
for each named agent in order, without duplicates, the run SHALL open one
task — a message with no task id and metadata `state` `input-required`,
`round` `1`, `to` the agent, `skill` `review-finding`, and `head` the PR's
`headRefOid` when it can be read — whose text asks for a review of the head
and for each finding as a task to this agent, unless a task already exists
whose opener is this agent and whose first message is addressed to that
agent. These posts SHALL write nothing on stdout.

#### Scenario: The first review task is opened once
- **WHEN** `run 7 --role author --agent author-a --request-review reviewer-b`
  runs on an open PR with head `abc1234def` and no task, and the PR merges on
  the first watch
- **THEN** exactly one task is opened, addressed to `reviewer-b` with skill
  `review-finding`, state `input-required`, and metadata `head` `abc1234def`,
  and stdout is the one summary line

#### Scenario: An existing request is not repeated
- **WHEN** the same run starts and a task opened by `author-a` to
  `reviewer-b` already exists
- **THEN** no task is opened

#### Scenario: A reviewer cannot request a review
- **WHEN** `run 7 --role reviewer --request-review x` runs
- **THEN** the exit code is `2` and nothing is read from or posted to GitHub

### Requirement: Any push to the head requests a re-review
id: room-run-rereview

While the role is `author`, the run SHALL remember the last head it read, starting from a `headRefOid` read made after the kick-off. After every watch slice that surfaces no task, and after every turn that returns ok, the run SHALL read the head again. When that read succeeds, the remembered head is non-empty, and the two differ, the run SHALL open one re-review task, shaped as the kick-off task with `head` the new SHA and text naming it, to each target lacking one for that head, whoever moved the head. It SHALL then remember the new head. The targets are the `--request-review` agents plus every agent whose card role is `reviewer` and who opened a task first addressed to this agent, excluding this agent. A target lacks one when no task exists whose opener is this agent, whose first message is addressed to the target, and whose first message's `head` equals the new SHA. If a head read fails, then the run SHALL warn once on stderr, open no re-review for that read, keep the remembered head, and continue. A reviewer or `ci` run SHALL open no re-review.

#### Scenario: A fix push opens one re-review to the reviewer who filed it
- **WHEN** an author run's fake runner answers a finding task opened by `reviewer-b` (card role `reviewer`) and moves the fake head from `aaa1111` to `bbb2222`
- **THEN** one task is opened to `reviewer-b` with skill `review-finding` and metadata `head` `bbb2222`

#### Scenario: A push by someone else between slices opens one re-review
- **WHEN** an author run started with `--request-review reviewer-b` sees the fake head move from `aaa1111` to `bbb2222` during a watch slice, with no turn run
- **THEN** exactly one task is opened to `reviewer-b` at `head` `bbb2222`, beyond the kick-off task

#### Scenario: The author's own push is requested once
- **WHEN** an author turn moves the head to `bbb2222` and the run then watches more slices
- **THEN** exactly one re-review task to each target exists at `head` `bbb2222`

#### Scenario: The re-review is idempotent per head
- **WHEN** a task opened by `author-a` to `reviewer-b` with `head` `bbb2222` already exists when the head moves to `bbb2222`
- **THEN** no task is opened

#### Scenario: A turn that pushes nothing requests nothing
- **WHEN** an author turn leaves the head at `aaa1111`
- **THEN** no task is opened

#### Scenario: A reviewer run never requests a re-review
- **WHEN** a reviewer run's head moves during a turn or between slices
- **THEN** no task is opened by the run

### Requirement: Hand-off tests, docs, and version
id: room-run-handoff-docs

The preflight, kick-off, and re-review SHALL be covered offline in
`plugins/s/skills/room/tests/test_room_run.py` and
`plugins/s/skills/build/tests/test_session_driver.py`, every room run test
injecting a fake preflight so no real harness starts. `docs/room-run.md`
SHALL stay a lint-clean how-to that shows `--request-review`, the manual
`shipd room message <pr> --new --to <reviewer> --skill review-finding` step,
the re-review after a push, and the preflight with its sign-in command.
`plugin.json` SHALL carry a version one patch above `main`'s.

#### Scenario: Suites pass offline
- **WHEN** the room and build test suites run
- **THEN** each reports `OK`

#### Scenario: The how-to lints clean and names the hand-offs
- **WHEN** `docs_lint.py docs/room-run.md` runs
- **THEN** it exits `0`, and the doc contains `--request-review`,
  `--skill review-finding`, `re-review`, and `claude auth login`

### Requirement: An author run acts on the CI reviewer's fix-required review
id: room-run-ci-findings

While the role is `author`, the run SHALL watch in slices of at most four `--interval` periods, and a slice that surfaces no task SHALL not end the run while budget remains. While `--ci-reviewer` (default `github-actions[bot]`) is also non-empty, after the kick-off and after every slice that surfaces no task, the run SHALL read the pull request's reviews. A review matches when its author login equals `--ci-reviewer` ignoring case, its commit is the current head, and its body carries `<!-- shipd-verdict: fix-required -->`. For the newest matching review not yet handled in this run, the run SHALL mark every matching review handled and spend one resumed author turn whose prompt names the review and tells the author to fix and push, or reply with the reason. That turn SHALL count toward `--max-turns` and SHALL open re-reviews on a moved head exactly as a task turn does. A failed reviews read SHALL warn once on stderr and run no turn. A reviewer or `ci` run SHALL read no reviews and keep a single watch over the remaining budget. An author run with an empty `--ci-reviewer` SHALL read no reviews and still watch in slices.

#### Scenario: A fix-required review of the head starts one turn
- **WHEN** an author run sees a `github-actions[bot]` review of the head carrying the fix-required marker
- **THEN** it runs one turn whose prompt names that review, and a second check runs no further turn for it

#### Scenario: Other reviews start nothing
- **WHEN** the only reviews are a ship-it review, a fix-required review of an older head, or one by another login
- **THEN** the run spends no turn on them

#### Scenario: A pushed fix requests a re-review
- **WHEN** the CI turn moves the head and the run was started with `--request-review reviewer-b`
- **THEN** a re-review task is opened to `reviewer-b` at the new head

#### Scenario: A reviewer run never reads reviews
- **WHEN** a reviewer run waits for tasks
- **THEN** it makes no reviews read

#### Scenario: An empty CI reviewer still slices
- **WHEN** an author run with `--ci-reviewer ""`, `--interval 5`, and `--budget 100` waits with no task
- **THEN** every watch timeout is at most `20`, more than one watch runs, and no reviews read is made

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
