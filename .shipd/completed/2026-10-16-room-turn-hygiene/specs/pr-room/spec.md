## MODIFIED Requirements

### Requirement: Room verbs reach GitHub only through the gh seam
id: room-gh-seam
base: 039c543f20d7

`plugins/s/skills/room/scripts/room.py` SHALL expose `main(argv=None,
gh=None)` whose `gh` is a runner `gh(args, input=None) -> (rc, stdout,
stderr)` defaulting to a `subprocess` call of the `gh` CLI, and every GitHub
read or write SHALL go through that runner. The module SHALL import only
the standard library, `room_schema` (its sibling), and the engine's
`spec_common` and `cli_common` from `skills/build/scripts/`. Every verb SHALL
accept a pull request URL as `<pr>` and a `--repo <owner/name>` flag. A room
SHALL be resolved with one function that takes the repository from the pull
request URL's path first, then from `--repo`, and otherwise from `gh repo
view --json nameWithOwner` in the working directory; `gh pr view <pr> --json
number,url` SHALL carry `--repo <repo>` whenever the repository came from a
URL or the flag. If the URL and `--repo` name different repositories, then
the verb SHALL print one `Error:` line naming both and exit `1`. The
context id is `<owner>/<repo>#<number>`. The room's
comments SHALL be read as the union of `gh api
repos/<repo>/issues/<n>/comments?per_page=100 --paginate --slurp` and `gh api
repos/<repo>/pulls/<n>/comments?per_page=100 --paginate --slurp` — issue
comments carry room traffic, review comments carry the semantic-review
gate's finding tasks and the replies on their threads — the returned pages flattened and the union ordered
by `created_at` and then by comment id, because GitHub numbers issue
comments and review comments in separate sequences, so a reply posted as
an issue comment onto a review-comment opener must still follow its
opener; each comment is parsed with
`room_schema.parse_comments(body, author=<user.login>)` so a comment carrying
both a card and a Message contributes both. If a comment's
marker raises `SchemaError`, then the verb SHALL print one
`WARNING: comment <id>: <reason>` line on stderr and skip it. A failed `gh`
call SHALL be reported as a single `Error: <reason>` line and exit `1`;
invalid arguments SHALL exit `2` with usage text, per `cli-conventions`.

#### Scenario: Comments are paged and flattened
- **WHEN** the fake runner answers the comments call with two slurped pages
- **THEN** `list` reports the cards and tasks of both pages, and the recorded
  call carries `--paginate` and `--slurp`

#### Scenario: A reply follows its opener across endpoints
- **WHEN** a review comment with id `900` created at `10:00` opens a task
  and an issue comment with id `50` created at `10:05` replies to it
- **THEN** the room read orders the opener before the reply and the task
  holds both messages, the reply last

#### Scenario: A failed gh call is one Error line
- **WHEN** the runner returns a non-zero code for `gh pr view`
- **THEN** stderr carries a single `Error: ` line and the exit code is `1`

#### Scenario: A malformed marker is skipped with a warning
- **WHEN** one comment holds `<!-- shipd-room {not json} -->`
- **THEN** `list` prints `WARNING: comment <id>:` on stderr, exits `0`, and
  reports every other comment

#### Scenario: A URL resolves with no repository lookup
- **WHEN** `watch https://github.com/o/r/pull/7 --once` runs
- **THEN** the context id is `o/r#7`, no `gh repo view` call is recorded, and
  every recorded `gh pr view` carries `--repo o/r`

#### Scenario: The flag supplies the repository
- **WHEN** `list 7 --repo o/r` runs
- **THEN** the context id is `o/r#7`, `gh pr view` carries `--repo o/r`, and
  no `gh repo view` call is recorded

#### Scenario: Neither falls back to the working directory
- **WHEN** `list 7` runs with no URL and no `--repo`
- **THEN** one `gh repo view` call supplies the repository

#### Scenario: A conflict is refused
- **WHEN** `list https://github.com/o/r/pull/7 --repo x/y` runs
- **THEN** stderr carries one `Error: ` line naming `o/r` and `x/y`, the exit
  code is `1`, and no comments are read

### Requirement: List reports cards and tasks
id: room-list-verb
base: 701cf4d9b7cc

`room.py list <pr> [--json] [--open]` SHALL read the room once and print, in
text mode, a `room <context>` header, a `cards:` block with one line per card
(`name`, `harness`, `skills`, `version`) and a `tasks:` block with one line
per `Task` from `room_schema.build_tasks` (`#<id>`, `state`, `from <opener>`,
`to <addressee|->`, `round <n>`, `last <last_agent>`, and `skill <s>` when
set); with `--json` it SHALL print one object `{"context", "cards": [card
dicts], "tasks": [{"id", "state", "opener", "to", "round", "reason",
"last_agent", "skill", "messages": <count>}]}`. With `--open`, the tasks
block and the JSON `tasks` array SHALL hold only tasks whose state is
`working` or `input-required`; the exit code is unchanged. A room with no
cards or no tasks SHALL print `(none)` under that block.

#### Scenario: Two cards and one open task
- **WHEN** the PR holds cards for `codex-a` and `claude-b` and a task opened
  by `codex-a` to `claude-b` at `input-required`
- **THEN** text output lists both cards and `#<id>  input-required  from
  codex-a  to claude-b  round 1  last codex-a`, and `--json` carries the
  same two cards and one task with `messages` `1`

#### Scenario: Human comments are not tasks
- **WHEN** the PR holds only unmarked comments
- **THEN** both blocks print `(none)` and the exit code is `0`

#### Scenario: Open keeps only unfinished tasks
- **WHEN** the PR holds one `completed`, one `working`, and one
  `input-required` task and `list --open --json` runs
- **THEN** `tasks` holds exactly the `working` and `input-required` tasks

#### Scenario: A clean room lists no open task
- **WHEN** every task is `completed` and `list --open --json` runs
- **THEN** `tasks` is `[]` and the exit code is `0`

### Requirement: Watch exit semantics
id: room-watch-exit
base: fea9e3b72d08

After a poll that surfaced no task, `watch` SHALL end when `--once` is set
or when `--timeout` is set and the injectable monotonic clock reports at
least that many seconds since the watch started; otherwise it SHALL call the
injectable `sleep` with `--interval` and poll again. A watch that ends
without surfacing a task SHALL print `watch: no actionable task on <context>
(cursor <n>)` on stderr, print nothing on stdout, and exit `0`, so a caller
branches on empty stdout. Each poll SHALL also read the pull request's state
through `gh pr view <number> --json state --repo <repo>`; when it is `MERGED`
or `CLOSED`, then after printing any task surfaced in that poll, `watch`
SHALL print one stdout line `{"closed": "merged"|"closed", "context":
<context>, "cursor": "<issue>:<review>", "open": [...]}`, where `open` lists
every task in `working` or `input-required` as `{"task", "state", "to",
"skill"}` and is `[]` when none; when `open` is not empty it SHALL first print
`watch: <n> unresolved task(s): #<id> <state>, ...` on stderr; it SHALL then
print `watch: <context> is <merged|closed>; the room is closed` on stderr and
exit `0`. A `KeyboardInterrupt` SHALL exit `130`
with no traceback; a failed `gh` call SHALL be reported as a single `Error:
<reason>` line with exit `1`, exactly as the other verbs report it.
`main(argv=None, gh=None, sleep=time.sleep, clock=time.monotonic)` SHALL
accept the two seams as keyword arguments.

#### Scenario: Once with nothing exits zero and empty
- **WHEN** `watch 7 --once` runs on an open PR with no actionable task
- **THEN** stdout is empty, stderr ends with the `watch: no actionable task`
  line naming the cursor, and the exit code is `0`

#### Scenario: Timeout ends the watch
- **WHEN** `watch 7 --timeout 60 --interval 20` runs with an injected clock
  advancing 25 seconds per call and no task ever appears
- **THEN** `sleep` is called until the clock passes 60, the verb exits `0`
  with empty stdout,
  and the comments read was recorded once per poll

#### Scenario: Failed read is fatal
- **WHEN** the runner answers the comments read with a non-zero code
- **THEN** the verb prints one `Error: ` line and exits `1` without sleeping

#### Scenario: Merged pull request ends the watch
- **WHEN** `watch 7 --timeout 600` runs and the runner answers the state read
  with `{"state": "MERGED"}` and no task is actionable
- **THEN** stdout holds exactly one line whose `closed` is `merged` and whose
  `open` is `[]`, stderr ends with the `the room is closed` line, `sleep` is
  never called, and the exit code is `0`

#### Scenario: The closed line lists unresolved tasks
- **WHEN** the pull request is `MERGED` and one task sits at `input-required`
  and another at `completed`
- **THEN** the closed line's `open` holds only the `input-required` task with
  its `task`, `state`, `to`, and `skill`, and stderr prints the `unresolved
  task` line before the `the room is closed` line

#### Scenario: The state read carries the repository
- **WHEN** `watch https://github.com/o/r/pull/7 --once` runs
- **THEN** the recorded `gh pr view 7 --json state` call carries `--repo o/r`
