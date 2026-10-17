## MODIFIED Requirements

### Requirement: Summary comment carries the gate's room card
id: gate-room-summary
base: dcfa49297dfe
Dropped: Card and Message parse back

When `review_gate.py post` renders the summary comment, the system SHALL
insert, directly above the review footer (or as the body's last line when
no footer renders), one `<!-- shipd-room-card <json> -->` line produced by
`room_schema.render_marker` from `plugins/s/skills/room/scripts/room_schema.py`,
and SHALL leave the hidden `<!-- shipd-semantic-review -->` marker as line 1,
the brand line as the first non-blank line after it, and the footer as the
last line. The card SHALL carry `name` `semantic-review`, `skills`
`["semantic-review"]`, `description` `shipd semantic-review gate`, and
`version` read from the plugin manifest (empty when unreadable). The summary
SHALL carry no `<!-- shipd-room <json> -->` Message line, so `room.py list`
and `room.py watch` show no task for the summary while its card stays in
the cards block. `render_summary` SHALL emit the card line only when given a
`room` argument, and `post` SHALL pass one on every upsert — the first post,
the folded re-post, and the fast-pass re-upsert alike — so a body rendered
without `room` stays byte-identical to today's.

#### Scenario: Markers sit between the body and the footer
- **WHEN** `render_summary` runs with `files` and a `room` argument
- **THEN** line 1 is `<!-- shipd-semantic-review -->`, the brand line follows
  it, the last line is the `Reviewed …` footer, and the line directly above
  the footer's blank separator is the card marker

#### Scenario: Card parses back and no Message renders
- **WHEN** the summary rendered with a `room` argument is passed to
  `room_schema.parse_comments`
- **THEN** it yields exactly one object, an `AgentCard` named
  `semantic-review` with skill `semantic-review`, and the body contains no
  `<!-- shipd-room ` text

#### Scenario: Rendering without a room is unchanged
- **WHEN** `render_summary` runs without a `room` argument
- **THEN** the body contains no `shipd-room` text

#### Scenario: Every upsert carries the markers
- **WHEN** `post` runs with an inline review that is rejected once, so the
  summary is upserted three times
- **THEN** the final summary body carries exactly one card marker and no
  Message marker

#### Scenario: The room lists the gate's card and no summary task
- **WHEN** `room.py`'s room read (`_parse_room`) reads the summary and the
  one anchored inline comment a `post` published
- **THEN** its cards include `semantic-review` and its tasks hold only the
  finding's task

### Requirement: Anchored findings open room tasks
id: gate-finding-room-task
base: 98c1c7de0366

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
- **THEN** each of the two review comments carries one `<!-- shipd-room `
  Message line, the summary carries one card line and no Message line, and
  no other room marker is posted

#### Scenario: Inline body without a room is unchanged
- **WHEN** `_inline_body` renders a finding without a `room` argument
- **THEN** the body contains no `shipd-room` text

## ADDED Requirements

### Requirement: A re-posted summary keeps its earlier reviews
id: summary-earlier-reviews

When `review_gate.py post` runs on a pull request that already holds a
summary comment, the system SHALL render the new summary with a collapsed
block `<details><summary>Earlier reviews</summary>` … `</details>` placed
after the fast-pass line and before the head and card lines, listing one
`- <verdict> — `<sha7>` — <YYYY-MM-DD HH:MM> UTC` line per earlier review,
newest first: first the previous summary (its `## Findings:` verdict text,
the first 7 characters of its recorded head, and its comment `updated_at`,
else `created_at`), then every entry of the previous summary's own
Earlier-reviews block in order. Every summary `post` renders SHALL record
its head commit in a hidden `<!-- shipd-semantic-review-head <sha> -->`
line. If the previous summary records no head, then its entry SHALL name
`unknown` for the sha; if it has no verdict header, `verdict unknown`; if
it has no timestamp, the time segment SHALL be omitted. The first post on a
pull request SHALL carry no Earlier-reviews block. The list SHALL be
computed once per `post`, before its first upsert, so the run's own fold
and fast-pass re-upserts never add an entry.

#### Scenario: First post has no earlier list
- **WHEN** `post` runs on a pull request with no summary comment
- **THEN** the summary contains no `Earlier reviews` text and carries one
  head line naming the PR head

#### Scenario: A pass after a fix-required keeps the old verdict
- **WHEN** `post` publishes a `changes-requested` review on head `aaaaaaa…`
  and then a `pass` review on head `bbbbbbb…`
- **THEN** the summary's header is `## Findings: ✅ Ship it` and its
  Earlier-reviews block holds exactly one line, starting
  `- ❌ Fix required — `aaaaaaa``

#### Scenario: Entries carry forward newest first
- **WHEN** three reviews post in turn on heads `aaaaaaa…`, `bbbbbbb…`, and
  `ccccccc…`
- **THEN** the Earlier-reviews block lists the `bbbbbbb` entry, then the
  `aaaaaaa` entry, and the summary still carries one Earlier-reviews block

#### Scenario: The time comes from the comment stamp
- **WHEN** `earlier_reviews` reads a previous summary whose `updated_at` is
  `2026-10-17T12:34:56Z`
- **THEN** its entry ends `— 2026-10-17 12:34 UTC`

#### Scenario: A legacy summary without a head record
- **WHEN** `earlier_reviews` reads a previous summary carrying no head line
- **THEN** its entry names `` `unknown` `` for the sha
