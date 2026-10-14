## 1. Skill scaffold, ci step, version

- [x] 1.1 [req: room-schema-tests] Create `plugins/s/skills/room/tests/test_room_schema.py`
      with the `HERE`/`SCRIPTS` `sys.path` prologue from
      `plugins/s/skills/review/tests/test_review_gate.py:22-27` and
      `import room_schema`; run `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v` and observe the ImportError — the module
      does not exist yet.
- [x] 1.2 [req: room-schema-tests] Add a `Run room test suite` step to
      `.github/workflows/ci.yml` directly after the workspace suite step
      (line 76), running `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v`.
- [x] 1.3 [req: room-schema-tests] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.289` to `0.6.290`.
- [x] 1.4 [req: room-marker-format] In the test file, add a test that reads
      `room_schema.py`'s source and asserts no `import subprocess`,
      `import urllib`, `import http`, or `import socket` line; and a test that
      imports `room_schema` and asserts `STATES`,
      `TERMINAL_STATES`, `ROLES`, `MESSAGE_MARKER == "shipd-room"`,
      `CARD_MARKER == "shipd-room-card"` exist.

## 2. Marker format

- [x] 2.1 [req: room-marker-format] Add tests: an agent Message with text
      `a --> b` renders a first line matching `^<!-- shipd-room \{.*\} -->$`
      containing no other `-->`, and `parse_comment(rendered)` equals the
      Message; a body `**● high — x**\n\n<marker line>` parses to the Message;
      `parse_comment("looks good", author="octocat")` returns a user Message
      (agent `octocat`, text `looks good`, `task_id None`);
      `<!-- shipd-room {not json} -->` raises `SchemaError`; a body carrying
      a card marker then a Message marker makes `parse_comments(body)` return
      `[AgentCard, Message]` in that order, and `parse_comments("looks good",
      author="octocat")` returns a one-element list holding the user Message.
- [x] 2.2 [req: room-marker-format] Create
      `plugins/s/skills/room/scripts/room_schema.py` with a module docstring
      stating it is pure stdlib with no I/O; define `MESSAGE_MARKER`,
      `CARD_MARKER`, `STATES`, `TERMINAL_STATES`, `ROLES`,
      `class SchemaError(ValueError)`, `class InvalidTransition(SchemaError)`,
      `_dump(obj)` (compact sorted JSON with `>` replaced by `\u003e`),
      `render_marker(kind, obj)` returning `<!-- <kind> <json> -->`, and
      `find_marker(body)` returning `(kind, dict)` for the first
      `<!-- shipd-room(-card)? … -->` found by `re.search`, raising
      `SchemaError` on bad JSON, or `None` when absent.
- [x] 2.3 [req: room-marker-format] In `room_schema.py` add
      `parse_comment(body, author=None)`, `parse_comments(body, author=None)`
      (every marker in body order as a list; `parse_comment` returns its first
      element), and `render_comment(obj)` delegating
      to the card/message converters of sections 3 and 4; the unmarked-body
      branch returns `Message(role="user", parts=({"kind": "text", "text":
      body.strip()},), context_id=None, agent=author, task_id=None)`. Run the
      section 2 tests until they pass.

## 3. Agent Card

- [x] 3.1 [req: room-agent-card] Add tests: a card `codex-reviewer`, harness
      `codex`, skills `("review-finding",)` renders a `shipd-room-card` first
      line and prose `**codex-reviewer** joined the room from codex — skills:
      review-finding`; a card marker without `name` raises `SchemaError`; a
      marker with key `securitySchemes` round-trips with the key in `extra`
      and back in the rendered JSON.
- [x] 3.2 [req: room-agent-card] In `room_schema.py` add `@dataclass
      AgentCard(name, description="", skills=(), version="", harness="",
      extra=field(default_factory=dict))`, `card_from_dict(d)` (validate
      non-empty `name`, coerce `skills` to a tuple of str, collect unknown keys
      into `extra`), `card_to_dict(card)` (known keys plus `extra`), and
      `_card_prose(card)` per the plan; wire both into
      `parse_comment`/`render_comment`. Run the section 3 tests until they pass.

## 4. Message

- [x] 4.1 [req: room-message-shape] Add tests: an agent Message (state
      `input-required`, to `codex-reviewer`, round 1) renders marker JSON whose
      `metadata` is exactly `{"round":1,"state":"input-required","to":"codex-reviewer"}`
      and holds no top-level `state`; the wire keys are `agent`, `contextId`,
      `metadata`, `parts`, `role`, `taskId`; `metadata.state` `open` raises
      `SchemaError`; missing `agent` or `contextId` on an agent message raises;
      `round` `0` raises; a `text` part plus a `data` part renders only the
      text and parses back with both parts; `Message.text` joins two text
      parts with a blank line.
- [x] 4.2 [req: room-message-shape] In `room_schema.py` add `@dataclass
      Message(role, parts, context_id, agent, task_id=None,
      metadata=field(default_factory=dict), extra=field(default_factory=dict))`
      with properties `state`, `to`, `round`, `reason`, `skill`, `text`;
      `message_from_dict(d)` mapping `contextId`/`taskId` to the field names,
      validating per the requirement, and collecting unknown keys into `extra`;
      `message_to_dict(m)` emitting the A2A wire keys plus `extra`; and
      `_message_prose(m)` returning `m.text`. Wire both into
      `parse_comment`/`render_comment`. Run the section 4 tests until they pass.

## 5. Task view

- [x] 5.1 [req: room-task-view] Add tests: entries `(10, opener a→b
      input-required round 1)`, `(11, user Message)`, `(12, reply taskId 10
      from b completed round 2)` yield one Task with id 10, opener `a`, state
      `completed`, to `None`, round 2, last_agent `b`, two messages; a lone
      Message with `taskId` 99 yields `[]`; an opener with `metadata.skill`
      `review-finding` yields `Task.skill == "review-finding"`.
- [x] 5.2 [req: room-task-view] In `room_schema.py` add `@dataclass
      Task(id, context_id, opener, skill, messages, state, to, round, reason,
      last_agent)` and `build_tasks(entries)` implementing the open/append/skip
      rules, with `round` defaulting to 1 when the last message carries none.
      Run the section 5 tests until they pass.

## 6. State machine and rounds

- [x] 6.1 [req: room-state-machine] Add tests: `next_state(None,
      "input-required")` and `next_state(None, "submitted")` return the
      request; `next_state(None, "working")` raises `InvalidTransition`;
      `next_state("submitted", "submitted")` raises; from each of
      `submitted`, `working`, `input-required` every other state is accepted;
      from each terminal state every request raises; `next_round` on a task at
      round 3 with last_agent `b` returns 3 for `b` and 4 for `a`;
      `at_round_cap(task_at_6_last_b, "a", 6)` is true and for `b` is false.
- [x] 6.2 [req: room-state-machine] In `room_schema.py` add `is_terminal`,
      `next_state`, `next_round`, and `at_round_cap` per the plan's
      Implementation. Run the section 6 tests until they pass.

## 7. Verification

- [x] 7.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v` and `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`; grep the output for `OK` (not the
      tail); run `python3 plugins/s/skills/build/scripts/version_guard.py
      --base main --head HEAD` and `python3
      plugins/s/skills/build/scripts/spec_lint.py room-schema`; all exit 0.
