# room-schema
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Add `room_schema.py`, the pure-stdlib A2A-shaped data model of the PR room:
Agent Card, Message, the Task view, hidden-marker parse/render, and the
six-state machine — with its unittest suite wired into `ci`.

### Motivation

Every later `pr-room` member — the `shipd room` verbs, `watch`, the skill, the
CI wake, and the gate's adoption — must speak one comment shape, and today no
module parses or renders a room comment, so the verb member cannot post or read
one. The epic orders the schema first because every other member depends on it.

### Details

- New `plugins/s/skills/room/scripts/room_schema.py`: dataclasses `AgentCard`,
  `Message`, `Task`; `parse_comment`, `render_comment`, `build_tasks`,
  `next_state`, `next_round`, `at_round_cap`; errors `SchemaError` and
  `InvalidTransition`. No I/O, no `subprocess`, no network.
- New `plugins/s/skills/room/tests/test_room_schema.py`, discovered by a new
  `Run room test suite` step in `.github/workflows/ci.yml`.
- Plugin version bump `0.6.289` → `0.6.290` in
  `plugins/s/.claude-plugin/plugin.json`.

Affected capabilities: `pr-room` (added). Impact: the two new files, `ci.yml`,
`plugin.json`; no other script imports the module yet.

### Non-goals

- No `gh` call, no verb, no `shipd` binary dispatch (`room-cli-verb`).
- No actionable-task predicate or polling (`room-watch`).
- No `room` config key, no `SKILL.md`, no harness body, no workflow template,
  no change to `review_gate.py`.

## Implementation

- **Wire format.** Line 1 of a room comment is `<!-- shipd-room <json> -->`
  (Message) or `<!-- shipd-room-card <json> -->` (Agent Card); `<json>` is
  `json.dumps(obj, separators=(",", ":"), sort_keys=True)` with every `>`
  replaced by `\u003e` so no text part can close the HTML comment. A blank line
  and the prose follow. Rejected: a fenced JSON block (epic).
- **Parse searches, render leads.** `parse_comment(body, author=None)` finds
  the first marker anywhere in the body (`re.search`, as
  `review_gate._FINDING_MARKER_RE` does) because a gate finding keeps its
  severity line first (`review_gate.py:571-575`); `render_comment` emits the
  marker as line 1. An unmarked body is a human message:
  `Message(role="user", parts=[text], agent=author, context_id=None,
  task_id=None)`. Malformed JSON or a failed validation raises `SchemaError`.
- **Agent Card.** `name` (non-empty, required), `description`, `skills`
  (tuple of skill-id strings — the verbs take `--skill S`; rejected: A2A
  `AgentSkill` objects, nothing supplies their fields), `version`, `harness`,
  `extra` (unknown keys, preserved). Prose: `**<name>** joined the room`, then
  ` from <harness>` and ` — skills: a, b` when set, then the description.
- **Message.** `role` (`user` | `agent`), `parts` (tuple of dicts; a part with
  `kind: text` carries `text`; other kinds are kept but not rendered),
  `context_id` (`<owner>/<repo>#<n>`), `agent`, `task_id` (int GitHub comment
  id, or `None` for a task opener), `metadata` (dict), `extra`. Properties
  `state`, `to`, `round`, `reason`, `skill` read `metadata`; `text` joins the
  text parts with blank lines and is the rendered prose. Wire keys are the
  A2A names `contextId`, `taskId`. Validation: `role` in `ROLES`; an agent
  message needs `agent`, `context_id`, and `metadata.state` in `STATES`;
  `round` an int ≥ 1 when present.
- **Task view.** `build_tasks(entries)` takes `(comment_id, Message)` pairs
  in comment order. An agent message with `task_id None` opens a task whose
  `id` is its own comment id; a message whose `task_id` names a known task is
  appended. `Task` carries `id`, `context_id`, `opener` (agent name), `skill`
  (opener's `metadata.skill`), `messages`, and from the last message `state`,
  `to`, `round`, `reason`, `last_agent`. Messages naming an unknown task are
  skipped — the caller may have paged only part of the PR.
- **State machine.** `next_state(current, requested)` is the only transition
  table: `None → submitted | input-required` (an opener addressed with `--to`
  opens straight at `input-required`); from any non-terminal state every state
  except `submitted` is allowed; `completed`, `failed`, `canceled` are
  absorbing — any request raises `InvalidTransition`. Rejected: requiring
  `working` before `completed`; it blocks a one-message reply and the gate's
  auto-disposition.
- **Rounds.** A round is a turn (Q2): the opener is round 1,
  `next_round(task, agent)` returns `task.round` when `agent == task.last_agent`
  and `task.round + 1` otherwise, and `at_round_cap(task, agent, max_rounds)`
  is `next_round(...) > max_rounds`. The poster writes `next_round` into
  `metadata.round`; the Task view reads the last message's value.

Risk: a later member renders a marker by hand and drifts from the parser;
guard by exposing `render_marker`/`find_marker` and round-tripping both in the
tests. A hand-edited marker raises `SchemaError`, which the verbs report.

## Questions and answers

### Q1: Where does the task state travel in a Message?
- **Question:** Options: (1) `metadata.state` beside `to` and `round`, keeping
  the top level pure A2A Message fields; (2) a top-level `state` field beside
  the epic's `agent` field. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** `metadata.state` — option 1. The epic already homes `to` and
  `round` under `metadata`, and A2A's Message has no state field of its own.
- **Queued:** q-pr-room-task-state-field-home
- **Relied on by:** room-gate-adoption

### Q2: What increments a task's round?
- **Question:** Options: (1) a round is a turn — the round advances when the
  posting agent differs from the previous message's agent; (2) a round is a
  message — every post advances it. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A round is a turn — option 1. One agent's `working` then
  `completed` share a round, so the default cap of 6 means six hand-overs,
  matching the epic diagram's single cap check per pickup.
- **Queued:** q-pr-room-round-increment-unit

### Q3: How are unknown marker keys treated?
- **Question:** Options: (1) ignore unknown keys and preserve them in `extra`
  so a round-trip keeps them; (2) reject a marker carrying unknown keys.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Preserve — option 1. A later plugin or another A2A speaker may
  add fields, and the brief names interoperability as the point of the shape.
- **Queued:** q-room-marker-unknown-keys

## Readiness attestation

### Problem and motivation

Every later `pr-room` member needs one shared parse/render/state module, and
none exists.

Evidence:

- Epic `pr-room` Design: "the schema has no dependency; the verbs depend on
  the schema … That order is the member order."
- `plugins/s/skills/` holds no `room/` directory.

### Scope and non-goals

The change adds the schema module, its tests, a CI step and the version bump;
verbs, watch, config, skill, workflow and gate stay out.

Evidence:

- Epic `pr-room` Changes table: `room-cli-verb`, `room-watch`, `room-skill`,
  `room-action-wake`, `room-gate-adoption` own the excluded surfaces.
- Epic Decision "Network code sits beside `review_gate.py`": the schema is
  "pure stdlib, no subprocess".

### Affected capabilities and files

One new capability and four files, because the module is new and only the CI
discover list and the manifest reference it.

Evidence:

- Capability `pr-room` (added).
- Files: `plugins/s/skills/room/scripts/room_schema.py` (new),
  `plugins/s/skills/room/tests/test_room_schema.py` (new),
  `.github/workflows/ci.yml:76` (new step after the workspace suite),
  `plugins/s/.claude-plugin/plugin.json:4` (version `0.6.289`).
- Marker precedent: `plugins/s/skills/review/scripts/review_gate.py:58`
  (line-1 marker), `:503-510` (search-anywhere finding marker), `:571-575`
  (severity line must stay first).
- Runnable premise: `python3 plugins/s/skills/build/scripts/version_guard.py
  --base main --head HEAD` → exit 0 on the untouched worktree; it compares the
  manifest version across any `plugins/s/` edit.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Marker position on parse (search anywhere) and the Task/round API: settled
  by investigation of the gate's finding body.
- State home in `metadata`: PLANNER default, Q1.
- Round-per-turn counting: PLANNER default, Q2.
- Unknown keys preserved: PLANNER default, Q3.
