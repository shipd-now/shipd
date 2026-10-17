## MODIFIED Requirements

### Requirement: List reports cards and tasks
id: room-list-verb
base: c5d1ed690e7f

`room.py list <pr> [--json] [--open]` SHALL read the room once and print, in
text mode, a `room <context>` header, a `cards:` block with one line per card
(`name`, then `role <r>` when the card has a role, then `harness <h>` when
the card has a harness, then `skills <s|->` and `version <v|->`, separated
by two spaces) and a `tasks:` block with one line
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

#### Scenario: Card line shows the role and omits an unset harness
- **WHEN** the PR holds a card `claude-b` with role `author` and no harness,
  and a card `codex-a` with harness `codex` and no role
- **THEN** the text card lines are `claude-b  role author  skills -  version
  -` and `codex-a  harness codex  skills -  version -`, and neither line
  contains `harness -` or `role -`

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
