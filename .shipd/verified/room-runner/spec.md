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
