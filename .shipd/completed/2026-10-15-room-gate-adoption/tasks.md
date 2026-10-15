## 1. Precondition and version

- [x] 1.1 [req: gate-room-tests] Merge `main` into the change branch after
      `room-schema`, `room-cli-verb`, and `room-watch` have merged; from
      `plugins/s/skills/room/scripts/` confirm `python3 -c "import
      room_schema"` exits 0 and the module exposes `render_marker`,
      `find_marker`, `parse_comment`, `card_to_dict`, `message_to_dict`,
      `build_tasks`, `AgentCard`, `Message`, `MESSAGE_MARKER`, `CARD_MARKER`.
      Stop and report if any symbol is missing.
- [x] 1.2 [req: gate-room-tests] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to one patch above the value
      `main` carries.
- [x] 1.3 [req: gate-room-tests] In
      `plugins/s/skills/review/tests/test_review_gate.py` add `ROOM_SCRIPTS`
      (`plugins/s/skills/room/scripts/`, two levels up from `HERE` then down) to `sys.path` beside `SCRIPTS` (line 25-27),
      `import room_schema`, and a source test asserting `review_gate.py`
      inserts `plugins/s/skills/room/scripts/` on `sys.path` and imports `room_schema`,
      with no import outside the standard library and that module. Run it
      and observe it fail.
- [x] 1.4 [req: gate-room-tests] In `review_gate.py` add `HERE`,
      `ROOM_SCRIPTS = HERE/../../room/scripts` inserted on `sys.path`, and
      `import room_schema` after the stdlib imports (line 42-48); add
      `ROOM_AGENT = "semantic-review"`, `ROOM_SKILL = "review-finding"`,
      `_plugin_version()` reading `plugins/s/.claude-plugin/plugin.json` (three levels above `HERE`)
      (`""` on any failure), and `_room(repo, number)` returning
      `{"context": "%s#%d" % (repo, number), "agent": ROOM_AGENT}`. Run the
      1.3 test until it passes.

## 2. Summary card and message

- [x] 2.1 [req: gate-room-summary] Add a `RoomSummaryTest` class: with
      `files` and `room={"context": "o/r#7", "agent": "semantic-review"}`,
      `render_summary` keeps `MARKER` as line 1, `BRAND_LINE` as the first
      non-blank line after it, the footer as the last line, and the lines at
      `[-4]`/`[-3]` are a `shipd-room-card` line then a `shipd-room` line
      with a blank at `[-2]`; without `files` the two lines are the body's
      last lines; `room_schema.parse_comment(card_line)` is an `AgentCard`
      named `semantic-review` with skills `("semantic-review",)`,
      description `shipd semantic-review gate`, version equal to the
      manifest's; `parse_comment(message_line)` is a `Message` with role
      `agent`, agent `semantic-review`, context_id `o/r#7`, task_id `None`,
      state `completed`, round 1, `metadata["verdict"]` the verdict,
      `metadata["status"]` the status state, text equal to
      `_status_description(review, disposition)`; `render_summary` without
      `room` yields no `shipd-room` substring. Observe the failures.
- [x] 2.2 [req: gate-room-summary] In `review_gate.py` add
      `_room_card_line(room)` (an `AgentCard` per the requirement rendered
      with `render_marker(CARD_MARKER, card_to_dict(card))`) and
      `_room_summary_line(room, review, state, disposition)` (the `Message`
      per the requirement rendered with `render_marker(MESSAGE_MARKER,
      message_to_dict(msg))`); extend `render_summary(..., room=None,
      status_state=None)` to append `["", card_line, message_line]` after the
      fast-pass line and before the footer block when `room` is given,
      computing `status_state` from `status_state(verdict, findings,
      disposition)` when not passed. Run the 2.1 tests until they pass.

## 3. Finding tasks

- [x] 3.1 [req: gate-finding-room-task] Add a `RoomFindingTest` class: for
      each severity, `_inline_body(f, room=ROOM)` still satisfies
      `parse_severity`, `_parse_what`, and `_extract_finding_hash` as before,
      `lines[-1]` is the finding marker, `lines[-2]` is blank, and
      `parse_comment(lines[-3])` is an agent Message with context_id
      `o/r#7`, task_id `None`, state `input-required`, `to` `None`, skill
      `review-finding`, round 1, text equal to `what`, and a part with kind
      `data` whose `data` holds `severity`, `path` `a.py`, `line` 5, `hash`
      equal to the body's finding hash, `why`, `fix`; a suggestion-carrying
      body keeps the suggestion fence before the room line; a
      `location_index` 1 body carries that location's path, line, and hash;
      `build_tasks([(101, m1), (102, m2)])` returns ids `[101, 102]`, opener
      `semantic-review`, state `input-required`, skill `review-finding`;
      `_inline_body(f)` without `room` has no `shipd-room` substring. Observe
      the failures.
- [x] 3.2 [req: gate-finding-room-task] In `review_gate.py` add
      `_room_finding_line(room, f, path, line, digest)` building the Message
      per the requirement, extend `_inline_body(f, suggestion=None,
      location_index=0, room=None)` to insert `["", room_line]` before the
      closing `["", "<!-- shipd-finding … -->"]` when `room` is given, and
      thread `room` through `_review_comment` and `_post_review`. Run the
      3.1 tests until they pass.

## 4. Post wiring

- [x] 4.1 [req: gate-room-summary, gate-finding-room-task] Add a
      `RoomPostTest` class over `FakeGh`: `post` of a `pass` review leaves a
      summary carrying exactly one `shipd-room-card` and one `shipd-room`
      line whose `contextId` is `o/r#7`; `post` of two anchored findings plus
      one `b.py:99` unanchorable finding records one review whose two
      comments each carry one `shipd-room` line and the summary carries one;
      with `review_fail_times=1` the final summary still carries both lines
      and the retry review carries no comments; a `post` run twice leaves one
      summary comment whose markers are still present after the PATCH.
      Observe the failures.
- [x] 4.2 [req: gate-room-summary, gate-finding-room-task] In `post`
      compute `room = _room(repo, number)` after `_resolve_repo`, pass
      `room=room, status_state=state` to all three `render_summary` calls
      (the first call computes `state` before rendering, so move the
      `status_state(...)` line above the first upsert) and `room` to both
      `_post_review` calls. Run the 4.1 tests until they pass.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and `python3 -m unittest discover -s
      plugins/s/skills/room/tests -v`; grep each output for `OK` (not the
      tail). Run `python3 plugins/s/skills/build/scripts/version_guard.py
      --base main --head HEAD` and `python3
      plugins/s/skills/build/scripts/spec_lint.py room-gate-adoption`; all
      exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 9.8k |
| (no tool) | 0 | 3.0k |
| Read | 7 | 1.3k |
| SubagentHandback | 8 | 74 |
| Write | 7 | 74 |
| Agent | 5 | 8 |
| **Total** | 114 | 14.4k |
