# room-gate-adoption
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Make `review_gate.py post` speak the PR room: the summary comment gains the
gate's Agent Card plus a Message, and every anchored inline finding gains a
Message that opens an `input-required` task any agent with the
`review-finding` skill can pick up.

### Motivation

A gate finding is readable only by `review_gate.py` itself, so an agent on
another harness watching the PR through `shipd room watch` never learns a
finding exists and cannot take it as a task.

### Details

- `plugins/s/skills/review/scripts/review_gate.py`: imports `room_schema`;
  `render_summary` and `_inline_body` take a `room` argument and emit the
  marker lines; `post` always passes one.
- `plugins/s/skills/review/tests/test_review_gate.py`: room-marker tests over
  the existing `FakeGh`.
- Plugin version advanced one patch above `main`'s value at build time.

Affected capabilities: `semantic-review` (modified — three ADDED
requirements). `pr-room` is consumed, not modified. Depends on `room-schema`,
`room-cli-verb`, and `room-watch` merging first; this plan re-specifies none
of their requirements.

### Non-goals

- No change to `<!-- shipd-finding -->`, the severity line, the verdict scan,
  `reply`, `autoreply`, `resolve`, `prior`, or the `semantic-review` status.
- No room marker from the Actions gate workflow
  (`plugins/s/integrations/copilot/copilot-review-gate.yml`): it renders its
  own bodies and never runs the poster.
- No task for a folded finding, no `completed` post when a thread resolves,
  no reply handling — the picking agent's flow (`room-skill`) owns those.
- No new `post` flag or config key.

## Implementation

- **Markers are opt-in at the renderer, always-on at `post`.**
  `render_summary(..., room=None, status_state=None)` and `_inline_body(...,
  room=None)` emit nothing new without `room`, so every existing render test
  stays byte-identical; `post` computes `room = {"context": "<repo>#<n>",
  "agent": ROOM_AGENT}` once and passes it to all three summary upserts and
  both review POSTs. Rejected: a `--room` flag — the epic adopts the marker
  unconditionally.
- **Placement honours the pinned frames.** Summary: `MARKER` line 1, brand
  line, body, fast-pass line, then `""`, card line, Message line, then the
  footer block — the footer stays last (`summary-review-footer`). Inline:
  severity line first, prose, suggestion fence, `""`, Message line, `""`,
  finding marker last (`IdentityMarkerTest`). `room_schema.parse_comment`
  searches anywhere, so neither marker needs line 1.
- **Card before Message.** The first-marker read sees the gate as a
  participant; the summary Message needs the multi-marker read assumed below.
- **No `taskId` on a finding Message (Q-investigation).** The review POST
  returns no per-comment ids, so the Message omits `taskId` and
  `build_tasks` takes the inline comment's own id as the task id. Rejected:
  a PATCH per comment to write the id the schema already derives.
- **Finding parts.** One text part (`what`) and one `{"kind": "data",
  "data": {severity, path, line, hash, why, fix}}` for that location, so a
  picker gets the identity hash without parsing prose. `metadata`:
  `round` 1, `skill` `review-finding`, `state` `input-required`, no `to`.
- **Gate identity (Q1).** `ROOM_AGENT = "semantic-review"`, a module
  constant; the card lists skill `semantic-review` (what the gate does),
  `description` `shipd semantic-review gate`, `version` from
  `HERE/../../../.claude-plugin/plugin.json` as `room.py join` reads it,
  empty on failure.
- **Summary Message (Q2).** State `completed`, round 1, `metadata.verdict`
  and `metadata.status` (the commit status state), text
  `_status_description(review, disposition)`; the in-place PATCH keeps its
  task id stable across re-posts.
- **Import path.** `review_gate.py` inserts `HERE/../../room/scripts` on
  `sys.path` and imports `room_schema` at module scope — a hard dependency.
  Markers come from `render_marker`, never hand-built.
- **Settled by the epic's consistency pass.** (1) `room-cli-verb`'s
  `_read_room` unions `pulls/<n>/comments` with `issues/<n>/comments`,
  ordered by id, so finding tasks reach `list`, `watch`, and `message`.
  (2) `room-schema` exposes `parse_comments` (every marker in body order), so
  a summary carrying card plus Message yields both. Both are written into
  those members' delta specs and tasks; this plan relies on them.

Risk: a re-post opens fresh tasks while earlier ones stay `input-required`;
the skill member decides what a picker does with a resolved thread's task.
Risk: schema helper names drift before merge; task 1.1 stops on a missing
symbol.

## Questions and answers

### Q1: What is the gate's room agent name?
- **Question:** Options: (1) the fixed module constant `semantic-review`, the
  status-context string, with no flag or environment override; (2) resolve
  like the room verbs (`--agent` → `SHIPD_ROOM_AGENT` → `room.agent`),
  falling back to `semantic-review`; (3) a `--room-agent` flag on `post`,
  default `semantic-review`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the gate is one fixed participant recognizable from
  its status check, and the caller's own `SHIPD_ROOM_AGENT` identity is a
  different agent that may itself pick up the gate's findings.
- **Queued:** q-pr-room-gate-agent-name

### Q2: What task state does the summary Message carry?
- **Question:** Options: (1) `completed`, with `verdict` and `status` in
  `metadata`; (2) `submitted`, an open unaddressed notice; (3)
  `input-required` to no one with no skill. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — only `input-required` is actionable, and a report
  nobody answers should not sit open in `shipd room list`; the per-finding
  tasks are the actionable surface.
- **Queued:** q-pr-room-gate-summary-task-state

## Readiness attestation

### Problem and motivation

A gate finding is parseable only by the gate, so no other agent can discover
or take it as a task.

Evidence:

- Epic `pr-room` Introduction: findings "speak a private format … that
  nothing but `review_gate.py` parses"; Decision "The gate adopts the room
  marker additively, last".
- `review_gate.py:503-511` (`_FINDING_MARKER_RE`) is the only reader of the
  finding marker.

### Scope and non-goals

The change touches the poster's two renderers and `post`, plus tests and the
version; the verdict contract, the thread verbs, the Actions workflow, and
the picker's flow stay out.

Evidence:

- Epic `pr-room` Non-goals: "No change to the gate's verdict contract".
- `copilot-review-gate.yml:746-760,855-866` renders bodies itself and never
  invokes `review_gate.py`.
- Epic Changes table rows `room-skill`, `room-action-wake`.

### Affected capabilities and files

One capability and three files, because the markers are rendered by two
existing functions, wired by `post`, pinned by the existing suite, and the
manifest carries the bump.

Evidence:

- Capability `semantic-review`: `gate-poster` (base `cef9c0c5d9b0`),
  `summary-brand-mark` (`e6c2c95d333d`), `summary-review-footer`
  (`7f6b69426d96`) fix the frames this delta keeps; the delta is ADDED only.
- Files: `plugins/s/skills/review/scripts/review_gate.py:42-48,359-417,
  563-613,732-751,754-839`, `plugins/s/skills/review/tests/test_review_gate.py:
  24-27,86-346,1464-1502`, `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/review/tests` → `Ran 283 tests`, `OK`.
- Runnable premise: `python3 plugins/s/skills/build/scripts/version_guard.py
  --base main --head HEAD` → exit 0 on the untouched worktree.
- Runnable premise: `python3 -c "import room_schema"` from
  `plugins/s/skills/review/scripts` → `ModuleNotFoundError`; the schema is
  unmerged, hence task 1.1.
- Runnable premise: `spec_status.py wiki-show --personal` → no personal
  store; the memory consultation was skipped.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Renderer opt-in with always-on `post`, marker placement, card-first order,
  omitted `taskId`, finding parts, import path: settled by investigation of
  `review_gate.py`, its tests, and the three sibling plans.
- Gate agent name: PLANNER default, Q1.
- Summary Message state: PLANNER default, Q2.
