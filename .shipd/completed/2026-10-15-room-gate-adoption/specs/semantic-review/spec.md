## ADDED Requirements

### Requirement: Summary comment carries the gate's room card and message
id: gate-room-summary

When `review_gate.py post` renders the summary comment, the system SHALL
insert, directly above the review footer (or as the body's last lines when
no footer renders), one `<!-- shipd-room-card <json> -->` line followed by one
`<!-- shipd-room <json> -->` line, both produced by
`room_schema.render_marker` from `plugins/s/skills/room/scripts/room_schema.py`,
and SHALL leave the hidden `<!-- shipd-semantic-review -->` marker as line 1,
the brand line as the first non-blank line after it, and the footer as the
last line. The card SHALL carry `name` `semantic-review`, `skills`
`["semantic-review"]`, `description` `shipd semantic-review gate`, and
`version` read from the plugin manifest (empty when unreadable). The Message
SHALL carry `role` `agent`, `agent` `semantic-review`, `contextId`
`<owner>/<repo>#<number>`, no `taskId`, one text part holding the status
description (`<verdict>: <counts>`), and `metadata` `{"round": 1, "state":
"completed", "status": <commit status state>, "verdict": <verdict>}`.
`render_summary` SHALL emit the two lines only when given a `room` argument,
and `post` SHALL pass one on every upsert — the first post, the folded
re-post, and the fast-pass re-upsert alike — so a body rendered without
`room` stays byte-identical to today's.

#### Scenario: Markers sit between the body and the footer
- **WHEN** `render_summary` runs with `files` and a `room` argument
- **THEN** line 1 is `<!-- shipd-semantic-review -->`, the brand line follows
  it, the last line is the `Reviewed …` footer, and the two lines directly
  above the footer's blank separator are the card marker then the Message
  marker

#### Scenario: Card and Message parse back
- **WHEN** the card line and the Message line are each passed to
  `room_schema.parse_comment`
- **THEN** the card is an `AgentCard` named `semantic-review` with skill
  `semantic-review`, and the Message is an agent Message with `task_id`
  `None`, `state` `completed`, `metadata.verdict` the review's verdict, and
  `metadata.status` the posted commit status state

#### Scenario: Rendering without a room is unchanged
- **WHEN** `render_summary` runs without a `room` argument
- **THEN** the body contains no `shipd-room` text

#### Scenario: Every upsert carries the markers
- **WHEN** `post` runs with an inline review that is rejected once, so the
  summary is upserted three times
- **THEN** the final summary body carries exactly one card marker and exactly
  one Message marker whose `contextId` is `<owner>/<repo>#<number>`

### Requirement: Anchored findings open room tasks
id: gate-finding-room-task

When `review_gate.py post` renders an anchored inline finding comment, the
system SHALL insert one `<!-- shipd-room <json> -->` line directly above the
blank line that precedes the closing `<!-- shipd-finding <hash> -->` marker,
leaving the severity marker as the body's first line and the finding marker
as its last. The Message SHALL carry `role` `agent`, `agent` `semantic-review`,
`contextId` `<owner>/<repo>#<number>`, no `taskId` (so `room_schema.build_tasks`
takes the inline comment's own id as the task id), two parts — a text part
holding `what` and a part `{"kind": "data", "data": {"severity", "path",
"line", "hash", "why", "fix"}}` for that location — and `metadata`
`{"round": 1, "skill": "review-finding", "state": "input-required"}` with no
`to`. A finding folded into the summary SHALL open no task. `_inline_body`
SHALL emit the line only when given a `room` argument; `parse_severity`,
`_parse_what`, and `_extract_finding_hash` SHALL read a room-marked body
exactly as an unmarked one.

#### Scenario: Inline body keeps its frame around the room line
- **WHEN** `_inline_body` renders a high finding with a `room` argument
- **THEN** `parse_severity` returns `high`, the last line is the finding
  marker, the line before it is blank, the line before that parses to an
  agent Message at `input-required` with skill `review-finding`, no `to`,
  text equal to `what`, and a data part whose `hash` equals
  `_extract_finding_hash` of the body

#### Scenario: Task id is the inline comment id
- **WHEN** two rendered inline Messages are fed to `build_tasks` as
  `(101, m1)`, `(102, m2)`
- **THEN** it returns tasks with ids `101` and `102`, opener `semantic-review`,
  state `input-required`, skill `review-finding`

#### Scenario: Posted review carries one task per anchored site
- **WHEN** `post` publishes two anchored findings and one unanchorable one
- **THEN** each of the two review comments carries one `shipd-room` line, the
  summary carries one, and no other `shipd-room` text is posted

#### Scenario: Inline body without a room is unchanged
- **WHEN** `_inline_body` renders a finding without a `room` argument
- **THEN** the body contains no `shipd-room` text

### Requirement: Gate room-marker tests and version
id: gate-room-tests

The room markers SHALL be covered in
`plugins/s/skills/review/tests/test_review_gate.py` through the existing
`FakeGh` seam with no network access, discovered by the `ci` workflow's
existing `Run review test suite` step; `review_gate.py` SHALL import
`room_schema` from `plugins/s/skills/room/scripts/` and nothing beyond the
standard library otherwise; and the change SHALL advance the plugin version
in `plugins/s/.claude-plugin/plugin.json` by one patch above the value `main`
carries.

#### Scenario: Review suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/review/tests -v`
  runs with no network
- **THEN** it reports `OK`, including the room-marker tests

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`
