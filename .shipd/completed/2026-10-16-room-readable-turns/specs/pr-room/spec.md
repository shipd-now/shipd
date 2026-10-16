## MODIFIED Requirements

### Requirement: Agent Card shape
id: room-agent-card
base: 9ad2ee39bfc7

An `AgentCard` SHALL carry `name` (required, non-empty), `description`,
`skills` (a tuple of skill-id strings), `version`, `harness`, and `extra`
holding every unknown marker key. The card prose SHALL be one line wrapped in
`<sub>` and `</sub>`, reading `**☕ shipd** · **<name>** joined the room`, followed by
` from <harness>` when `harness` is set and ` · skills: <a, b>` when
`skills` is non-empty, then the description on its own paragraph when set.

#### Scenario: Card renders its prose
- **WHEN** a card named `codex-reviewer` with harness `codex` and skills
  `review-finding` is rendered
- **THEN** line 1 is a `shipd-room-card` marker and the prose reads
  `<sub>**☕ shipd** · **codex-reviewer** joined the room from codex · skills: review-finding</sub>`

#### Scenario: Nameless card is rejected
- **WHEN** a `shipd-room-card` marker has no `name`
- **THEN** `parse_comment` raises `SchemaError`

#### Scenario: Unknown card keys survive a round-trip
- **WHEN** a card marker carries a key `securitySchemes`
- **THEN** the parsed card holds it in `extra` and re-rendering emits it again

### Requirement: Message shape
id: room-message-shape
base: 8f9f5069d0d5

A `Message` SHALL carry `role` (`user` or `agent`), `parts` (a tuple of part
dicts; a part with `kind` `text` carries `text`), `context_id`, `agent`,
`task_id` (an int, or `None` for a task opener), `metadata`, and `extra`. The
wire keys SHALL be the A2A names `role`, `parts`, `contextId`, `taskId`,
`agent`, `metadata`. The properties `state`, `to`, `round`, `reason`, and
`skill` SHALL read the matching `metadata` keys, and `text` SHALL join the text
parts with blank lines. The rendered prose of an agent message SHALL open with
a header line `**☕ shipd** · **<agent>**`, the ☕ shipd brand marking every
agent comment as shipd's, followed by ` → <to>` when `metadata.to` is set
and ` · <state>` when `metadata.state` is set, then a blank line, then
`text`; a `user` message's prose SHALL be `text` alone. Parsing SHALL read the
marker only, so the header never enters `text`. An agent message SHALL be
rejected with `SchemaError` when `agent` or `context_id` is empty, when
`metadata.state` is not one of `submitted`, `working`, `input-required`,
`completed`, `failed`, `canceled`, or when `metadata.round` is present and not
an int of at least 1.

#### Scenario: State lives in metadata
- **WHEN** an agent Message with state `input-required`, to `codex-reviewer`,
  round 1 is rendered
- **THEN** the marker JSON holds `"metadata":{"round":1,"state":"input-required","to":"codex-reviewer"}`
  and no top-level `state` key

#### Scenario: Unknown state is rejected
- **WHEN** a marker carries `metadata.state` `open`
- **THEN** `parse_comment` raises `SchemaError`

#### Scenario: Non-text parts are kept but not rendered
- **WHEN** a Message holds a `text` part and a part of kind `data`
- **THEN** the prose shows only the text under the header, and the parsed
  Message still holds both parts

#### Scenario: Agent prose names the speaker
- **WHEN** an agent Message from `copilot-ci` with state `completed`, to
  `builder`, and text `done` is rendered and parsed back
- **THEN** the prose's first line is `**☕ shipd** · **copilot-ci** → builder · completed`,
  the text follows after a blank line, and the parsed Message's `text` is
  exactly `done`

### Requirement: Message opens or advances a task
id: room-message-verb
base: 9308e29c74dd

`room.py message <pr> (--new | --task ID) [--to AGENT] [--state S]
[--skill S] [--max-rounds N] <text>` SHALL post a `Message` (`role` `agent`,
one text part, the room's context id) as an issue comment. With `--new`
the Message SHALL carry no `taskId`, `metadata.round` `1`, `metadata.skill`
from `--skill` when given, and `metadata.state` `next_state(None, S)` where
`S` defaults to `input-required` when `--to` is given and `submitted`
otherwise. With `--task ID` the id SHALL name a task in the room's
`build_tasks` view (else `Error: task <id> not found on <context>`, exit
`1`); the Message SHALL carry `taskId` `ID`, `metadata.round`
`next_round(task, agent)`, and `metadata.state` `next_state(task.state, S)`
where `S` defaults to `input-required` when `--to` is given and `working`
otherwise; an `InvalidTransition` SHALL be reported as `Error: task <id> is
<state>; no transition to <S>` with exit `1` and nothing posted. Before
posting a `--task` reply, if `at_round_cap(task, agent, max_rounds)` holds,
then the verb SHALL post instead a Message at state `failed` with
`metadata.reason` `round-cap` and text `round cap (<max_rounds>) reached`,
and SHALL exit `1` with `Error: round cap reached on task <id> — posted
failed (round-cap)`. `metadata.to` SHALL be set from `--to` when given.
When a `--task` reply's state is not `working` and the task's last comment is
an issue comment whose room Message was posted by the acting agent at state
`working`, then after posting the reply the verb SHALL delete that claim
comment through `gh api -X DELETE repos/<repo>/issues/comments/<id>`; if the
delete fails, then the verb SHALL print `warning: could not remove claim
comment <id>` on stderr and still succeed. On success the verb SHALL print
`{"comment": <id>, "task": <task id>, "state": <state>, "round": <n>, "url":
<html_url>}` on stdout and exit `0`.

#### Scenario: Addressed opener starts at input-required
- **WHEN** `message 7 --new --to claude-b "please check"` runs as `codex-a`
- **THEN** the posted marker holds no `taskId`, `metadata`
  `{"round":1,"state":"input-required","to":"claude-b"}`, and stdout's
  `task` equals the new comment id

#### Scenario: Reply advances the round for the other party
- **WHEN** task 10 is at `input-required`, round 1, last agent `codex-a`, and
  `message 7 --task 10 --to codex-a --state completed "done"` runs as
  `claude-b`
- **THEN** the posted marker holds `taskId` 10 and `metadata`
  `{"round":2,"state":"completed","to":"codex-a"}`

#### Scenario: Terminal task refuses a reply
- **WHEN** task 10 is `completed` and `message 7 --task 10 "more"` runs
- **THEN** nothing is posted and the verb exits `1` with the `no transition`
  Error line

#### Scenario: Cap posts failed and exits one
- **WHEN** task 10 is at round 6 with last agent `codex-a`, `--max-rounds 6`,
  and `message 7 --task 10 "again"` runs as `claude-b`
- **THEN** the only post carries `metadata` `{"reason":"round-cap","round":7,
  "state":"failed"}`, and the verb exits `1` with the `round cap reached`
  Error line

#### Scenario: Reply replaces the agent's own claim
- **WHEN** task 10's last comment is issue comment 30, a `working` Message
  from `claude-b`, and `message 7 --task 10 --to codex-a --state completed
  "done"` runs as `claude-b`
- **THEN** the runner records the reply's POST first and then a DELETE of
  `repos/<repo>/issues/comments/30`, and stdout's `comment` is the new
  comment's id

#### Scenario: Another agent's claim is left alone
- **WHEN** task 10's last comment is a `working` Message from `codex-a` and
  `message 7 --task 10 --state completed "done"` runs as `claude-b`
- **THEN** the runner records the POST and no DELETE

#### Scenario: Failed delete still succeeds
- **WHEN** the reply posts and the runner answers the DELETE with a non-zero
  code
- **THEN** stderr holds `warning: could not remove claim comment 30` and the
  verb exits `0`

### Requirement: Close posts the terminal message
id: room-close-verb
base: f8bf3e10b7b0

`room.py close <pr> --task ID [--state completed|canceled|failed]
[--reason TEXT] [text]` SHALL post a Message on task `ID` at
`next_state(task.state, S)` with `S` defaulting to `completed`,
`metadata.round` `next_round(task, agent)`, `metadata.reason` from
`--reason` when given, and the text defaulting to `closed: <S>` (plus ` —
<reason>` when set). It SHALL apply no round cap, SHALL report an
`InvalidTransition` exactly as `message` does, SHALL remove the acting
agent's own `working` claim comment exactly as `message` does, and SHALL
print the same JSON object `message` prints on success.

#### Scenario: Default close completes
- **WHEN** `close 7 --task 10` runs as `claude-b` on an `input-required` task
- **THEN** the posted marker holds `metadata.state` `completed` and no
  `reason`

#### Scenario: Close with a reason at the cap still posts
- **WHEN** task 10 is at round 6 with last agent `codex-a`, max rounds 6, and
  `close 7 --task 10 --state failed --reason stalled` runs as `claude-b`
- **THEN** the post carries `metadata` `{"reason":"stalled","round":7,
  "state":"failed"}` and the verb exits `0`

#### Scenario: Close replaces the agent's own claim
- **WHEN** task 10's last comment is issue comment 30, a `working` Message
  from `copilot-ci`, and `close 7 --task 10 --state failed --reason
  wake-runner-failed` runs as `copilot-ci`
- **THEN** the runner records the POST and then a DELETE of comment 30

### Requirement: Watch exit semantics
id: room-watch-exit
base: ab638884d0c6

After a poll that surfaced no task, `watch` SHALL end when `--once` is set
or when `--timeout` is set and the injectable monotonic clock reports at
least that many seconds since the watch started; otherwise it SHALL call the
injectable `sleep` with `--interval` and poll again. A watch that ends
without surfacing a task SHALL print `watch: no actionable task on <context>
(cursor <n>)` on stderr, print nothing on stdout, and exit `0`, so a caller
branches on empty stdout. Each poll SHALL also read the pull request's state
through `gh pr view <number> --json state`; when it is `MERGED` or `CLOSED`,
then after printing any task surfaced in that poll, `watch` SHALL print one
stdout line `{"closed": "merged"|"closed", "context": <context>, "cursor":
"<issue>:<review>"}`, print `watch: <context> is <merged|closed>; the room is
closed` on stderr, and exit `0`. A `KeyboardInterrupt` SHALL exit `130`
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
- **THEN** stdout holds exactly one line whose `closed` is `merged`, stderr
  ends with the `the room is closed` line, `sleep` is never called, and the
  exit code is `0`

### Requirement: Room wake workflow template
id: room-wake-workflow-template
base: 257e18027686

The plugin SHALL ship `plugins/s/integrations/copilot/room-wake.yml`, whose
first line is `# shipd-copilot v{version}`, triggered on `issue_comment` and
`pull_request_review_comment` with `types: [created]`, and composed of three
jobs. The `guard` job SHALL run only when `vars.SHIPD_ROOM_AGENT` is
non-empty, the comment body contains `<!-- shipd-room `, the comment's
`author_association` is `OWNER`, `MEMBER` or `COLLABORATOR`, and the event is
a review comment or an issue comment on a pull request; it SHALL bind
`github.token` and never `COPILOT_GITHUB_TOKEN`, check out the default
branch, and report not-actionable when the `COPILOT_GITHUB_TOKEN` secret is
absent. Otherwise it SHALL run the bundled
`.github/shipd-room/skills/room/scripts/room.py watch <pr> --once --since
<cursor>` as the agent `SHIPD_ROOM_AGENT` names — the cursor being the
`<issue>:<review>` pair `watch` accepts, `<id - 1>:0` for an `issue_comment`
trigger and `0:<id - 1>` for a `pull_request_review_comment` trigger — treat
empty stdout
as not actionable, and act only on the NDJSON line whose `comment` equals
the triggering comment id and whose `to` equals that agent; when acting it
SHALL `join` with `--harness copilot-cli` if no card of that name exists,
post `working` on the task, and output `actionable`, `pr`, `task`, `asker`
(the line's `last_agent`) and `text`. The `run` job SHALL depend on an
actionable guard, bind only `COPILOT_GITHUB_TOKEN`, check out
`refs/pull/<pr>/head` with `persist-credentials: false`, install
`@github/copilot@1.0.80`, run `copilot -p` with `-s` and `--allow-all-tools`
under a `timeout` defaulting to 600 seconds, with a prompt that asks for the
reply in GitHub-flavoured markdown with code in fenced blocks and no account
of the search steps taken, and output the reply truncated to
60000 characters. The `reply` job SHALL run with `if: always()` whenever the
guard was actionable, bind `github.token` and never `COPILOT_GITHUB_TOKEN`,
check out the default branch, read the reply only through `env:`, and post
via the bundled `room.py message <pr> --task <task> --to <asker>`: state
`input-required` with the marker stripped when the reply's last non-blank
line is exactly `<!-- shipd-room-reply: input-required -->`, else
`completed`. If the `run` job did not succeed or the reply is empty, then
the `reply` job SHALL instead post `close --task <task> --state failed
--reason wake-runner-failed`. Every `room.py` invocation SHALL run through
`/usr/bin/env -i` with an explicit `PATH=/usr/bin:/bin` and
`/usr/bin/python3 -B`.

#### Scenario: Addressed task is picked up
- **WHEN** the guard script runs with a stub `room.py` whose `watch` prints
  a line with `comment` equal to the event id and `to` equal to
  `SHIPD_ROOM_AGENT`
- **THEN** the guard outputs `actionable=true` with that task, asker and
  text, and the stub recorded a `message --task <id> --state working` call

#### Scenario: Other or empty lines are ignored
- **WHEN** the stub `watch` prints nothing, or a line for another comment
  id, or a line whose `to` names another agent
- **THEN** the guard outputs `actionable=false`, exits `0`, and the stub
  recorded no `message` or `join` call

#### Scenario: Reply marker selects input-required
- **WHEN** the reply script runs on a reply ending with the line
  `<!-- shipd-room-reply: input-required -->`
- **THEN** the stub recorded `message --task <id> --to <asker> --state
  input-required` with text that no longer holds the marker line

#### Scenario: Plain reply completes, failed run closes
- **WHEN** the reply script runs on a plain reply, and again with the run
  result `failure`
- **THEN** the first records `--state completed`; the second records `close
  --task <id> --state failed --reason wake-runner-failed`

#### Scenario: Credentials never share a job
- **WHEN** the template text is split into its three jobs
- **THEN** `COPILOT_GITHUB_TOKEN` is bound only in `run`, `github.token`
  only in `guard` and `reply`, and `run` checks out with
  `persist-credentials: false`

#### Scenario: The CLI runs silent and asks for markdown
- **WHEN** the template's `run` job is read
- **THEN** its `copilot -p` invocation carries `-s`, and its prompt names
  GitHub-flavoured markdown and fenced code blocks
