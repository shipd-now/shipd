## MODIFIED Requirements

### Requirement: Message opens or advances a task
id: room-message-verb
base: bdf44e8c1f32

`room.py message <pr> (--new | --task ID) [--to AGENT] [--state S]
[--skill S] [--max-rounds N] <text>` SHALL post a `Message` (`role` `agent`,
one text part, the room's context id) as an issue comment, except that a
`--task` reply or round-cap post on a finding task SHALL post on the
finding's review thread per `room-finding-thread-reply`. With `--new`
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
When a `--task` reply's state is not `working` and the task's last comment
holds a room Message for the task posted by the acting agent at state
`working`, then after posting the reply the verb SHALL delete that claim
comment, through `gh api -X DELETE repos/<repo>/issues/comments/<id>` for an
issue comment and `gh api -X DELETE repos/<repo>/pulls/comments/<id>` for a
review comment; if the delete fails, then the verb SHALL print `warning:
could not remove claim comment <id>` on stderr and still succeed. On success
the verb SHALL print `{"comment": <id>, "task": <task id>, "state": <state>,
"round": <n>, "url": <html_url>}` on stdout and exit `0`.

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

#### Scenario: A claim on a finding thread is deleted from the thread
- **WHEN** finding task 900's last comment is review comment 950, a
  `working` Message from `claude-b`, and `message 7 --task 900 --state
  input-required --to semantic-review "why?"` runs as `claude-b`
- **THEN** the runner records the thread reply's POST and then a DELETE of
  `repos/<repo>/pulls/comments/950`

#### Scenario: Another agent's claim is left alone
- **WHEN** task 10's last comment is a `working` Message from `codex-a` and
  `message 7 --task 10 --state completed "done"` runs as `claude-b`
- **THEN** the runner records the POST and no DELETE

#### Scenario: Failed delete still succeeds
- **WHEN** the reply posts and the runner answers the DELETE with a non-zero
  code
- **THEN** stderr holds `warning: could not remove claim comment 30` and the
  verb exits `0`

## ADDED Requirements

### Requirement: Finding task messages reply on the finding's thread
id: room-finding-thread-reply

A finding task SHALL be a task whose opening comment was read from the
review-comment endpoint (`repos/<repo>/pulls/<n>/comments`). Every Message
that `message --task`, `close`, `message`'s round-cap post, or `watch`'s
round-cap post puts on a finding task SHALL be created as a reply in that
review thread through `gh api -X POST repos/<repo>/pulls/<n>/comments
--input -` with the JSON `{"body": <rendered comment>, "in_reply_to": <task
id>}`, carrying the same room marker an issue comment would. A Message on
any other task, and every `--new` opener, SHALL remain an issue comment. The
verbs' stdout JSON SHALL be unchanged, its `comment` and `url` naming the
created review comment.

#### Scenario: A claim on a finding task posts on the thread
- **WHEN** review comment 900 opens a `review-finding` task from
  `semantic-review` and `message 7 --task 900 --state working "looking"`
  runs as `claude-b`
- **THEN** exactly one POST is recorded, on `repos/o/r/pulls/7/comments`,
  its payload's `in_reply_to` is `900`, its body's marker holds `taskId`
  900, and no issue comment is created

#### Scenario: An issue task still posts an issue comment
- **WHEN** issue comment 10 opens a task and `message 7 --task 10 --state
  completed "done"` runs
- **THEN** the POST is on `repos/o/r/issues/7/comments` and no `gh api
  graphql` call is recorded

#### Scenario: A round-cap post on a finding task replies on the thread
- **WHEN** `watch 7 --once --max-rounds 1` runs as `claude-b` with a card
  and finding task 900 is at the cap and addressed to `claude-b`
- **THEN** the `failed` (`round-cap`) Message is POSTed on
  `repos/o/r/pulls/7/comments` with `in_reply_to` 900

### Requirement: A completed finding task resolves its thread
id: room-finding-thread-resolve

When `message --task` or `close` posts a Message at state `completed` on a
finding task, then after posting the reply and removing any claim the verb
SHALL look up the review thread whose first comment's `databaseId` equals
the task id with `gh api graphql` over the pull request's
`reviewThreads(first:100)`, and, when that thread is not resolved, SHALL
resolve it by running `room_schema.RESOLVE_THREAD_MUTATION` with
`threadId` set to the thread's id. `review_gate.py` SHALL resolve threads
with that same constant. A Message at `canceled`, `failed`, or any
non-terminal state SHALL NOT resolve the thread. If no thread matches or
either GraphQL call fails, then the verb SHALL print `warning: could not
resolve the review thread for task <id>` on stderr and still exit `0` with
its usual stdout JSON.

#### Scenario: A completed close resolves the finding's thread
- **WHEN** finding task 900's thread `PRRT_1` is unresolved and `close 7
  --task 900 "Fixed in abc1234"` runs as `claude-b`
- **THEN** the runner records the thread reply's POST, then a `gh api
  graphql` lookup, then a `gh api graphql` call carrying
  `resolveReviewThread` and `threadId=PRRT_1`, and the verb exits `0`

#### Scenario: A canceled close leaves the thread open
- **WHEN** `close 7 --task 900 --state canceled` runs on that finding task
- **THEN** the reply is POSTed on the thread and no `resolveReviewThread`
  call is recorded

#### Scenario: An already resolved thread is not resolved again
- **WHEN** thread `PRRT_1` is already resolved and `close 7 --task 900` runs
- **THEN** the lookup is recorded and no `resolveReviewThread` call is

#### Scenario: A failed resolve still succeeds
- **WHEN** the runner fails the `resolveReviewThread` call after `close 7
  --task 900` posts its reply
- **THEN** stderr holds `warning: could not resolve the review thread for
  task 900`, stdout holds the reply's JSON, and the exit code is `0`

#### Scenario: No matching thread still succeeds
- **WHEN** the lookup returns no thread whose first comment is 900
- **THEN** stderr holds the same warning and the exit code is `0`
