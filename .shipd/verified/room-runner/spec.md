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

### Requirement: An author turn that moves the head requests a re-review
id: room-run-rereview

While the role is `author`, the run SHALL read the PR's `headRefOid` before
each turn and again after a turn that returns ok. When both reads succeed and
differ, the run SHALL open one re-review task, shaped as the kick-off task
with `head` the new SHA and text naming it, to each target lacking one for
that head. The targets are the `--request-review` agents plus every agent
whose card role is `reviewer` and who opened a task first addressed to this
agent, excluding this agent. A target lacks one when no task exists whose
opener is this agent, whose first message is addressed to the target, and
whose first message's `head` equals the new SHA. If a head read fails, then
the run SHALL warn on stderr, open no re-review for that turn, and continue.
A reviewer or `ci` run SHALL open no re-review.

#### Scenario: A fix push opens one re-review to the reviewer who filed it
- **WHEN** an author run's fake runner answers a finding task opened by
  `reviewer-b` (card role `reviewer`) and moves the fake head from `aaa1111`
  to `bbb2222`
- **THEN** one task is opened to `reviewer-b` with skill `review-finding`
  and metadata `head` `bbb2222`

#### Scenario: The re-review is idempotent per head
- **WHEN** a task opened by `author-a` to `reviewer-b` with `head` `bbb2222`
  already exists when that turn moves the head to `bbb2222`
- **THEN** no task is opened

#### Scenario: A turn that pushes nothing requests nothing
- **WHEN** an author turn leaves the head at `aaa1111`
- **THEN** no task is opened

#### Scenario: A reviewer run never requests a re-review
- **WHEN** a reviewer run's turn moves the head
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
