## ADDED Requirements

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
