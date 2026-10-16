## 1. Schema

- [x] 1.1 [req: room-agent-card, room-message-shape] In
      `plugins/s/skills/room/tests/test_room_schema.py`, update the card and
      message prose assertions to the new format and add tests: a card with
      role `reviewer`, harness `codex`, skills, login `mikkel` renders
      `### ☕ shipd · codex-reviewer · reviewer (for @mikkel)` then
      `<sub>joined the room from codex · skills: review-finding</sub>`; a card
      with no role and no login renders `### ☕ shipd · x`, and its marker has
      no `role` key; a `"role":"author"` marker round-trips; an agent message
      renders heading, then `→ builder · completed`, then the text, and
      parses back with `text == "done"`; a message with no `to` and state
      `working` has line 2 `working`. Run
      `python3 -B -m unittest plugins/s/skills/room/tests/test_room_schema.py`
      and observe failures.
- [x] 1.2 [req: room-agent-card, room-message-shape] In
      `plugins/s/skills/room/scripts/room_schema.py`, add `role: str = ""` to
      `AgentCard`, `"role"` to `_CARD_KEYS`, read it in `card_from_dict`
      with `_str_field`, emit it in `card_to_dict` only when non-empty. Add
      `ROLE_VALUES = ("author", "reviewer", "ci")` and
      `speaker_heading(agent, role="", login="")` returning
      `"☕ shipd · %s" % agent` plus ` · role` and ` (for @login)` when set.
      Change `_card_prose(card, login="")` and `_message_prose(m, login="",
      role="")` to the format in the delta spec (heading prefixed `### `),
      and `render_comment(obj, login="", role="")` to pass them (a card uses
      `obj.role`). Update the module docstring. Run the schema tests until
      they pass.

## 2. Room verbs

- [x] 2.1 [req: room-join-role, room-poster-identity] In
      `plugins/s/skills/room/tests/test_room.py`, make `FakeGh` answer
      `["api", "user"]` with `{"login": "bot"}` (counting calls, with an
      option to fail it), then add tests: `join --role author` posts a marker
      with `"role":"author"` and a heading `### ☕ shipd · codex-a · author
      (for @bot)`; `join --role boss` exits 2 and posts nothing; a rejoin
      without `--role` PATCHes a body with no `role` key; `message --new` as
      an agent whose card has role `author` heads its body with that role and
      `api user` was called once; a card without role gives
      `### ☕ shipd · <agent> (for @bot)`; with `api user` failing, `close`
      still posts, stderr has `warning:`, and the heading has no `(for @`;
      a `watch` round-cap post is headed and reads the login once across
      several capped tasks. Fix existing assertions on old prose. Run
      `python3 -B -m unittest plugins/s/skills/room/tests/test_room.py` and
      observe failures.
- [x] 2.2 [req: room-join-role, room-poster-identity] In
      `plugins/s/skills/room/scripts/room.py`, add `_login(gh, memo)`
      (`gh(["api", "user"])`, parse `login`, memoise in `memo`, on failure or
      empty login write one lower-case `warning: ...` line through
      `sys.stderr.write`, not `cli_common.warn`, which prints `WARNING:`,
      and return `""`) and
      `_card_role(cards, name)`. Give `_post_message` the keyword arguments
      `login=""` and `role=""` and pass them to `room_schema.render_comment`.
      In `cmd_join` render the card with `role=opts.role or ""` and the
      login; in `cmd_message` and `cmd_close` pass the login and the role
      from `_card_role(cards, agent)`; in `cmd_watch` create one memo and
      pass login and the agent's card role through `_cap_task`. Add
      `--role` with `choices=room_schema.ROLE_VALUES` to the `join` parser
      only. Update the module docstring. Run `test_room.py` until it passes.

## 3. Gate

- [x] 3.1 [req: gate-review-submission-body] In
      `plugins/s/skills/review/tests/test_review_gate.py`, make the fake `gh`
      answer `["api", "user"]` with a login, then add tests: the submitted
      review body's first line is `### ☕ shipd · semantic-review · reviewer
      (for @mikkel)`, its second line is `Semantic review: 2 inline comments.
      Full report in the summary comment.` for two comments, it never holds
      `see the summary comment for the full report`, and with `api user`
      failing the first line has no `(for @` and the event is `COMMENT`.
      Fix existing assertions on the old body. Run
      `python3 -B -m unittest plugins/s/skills/review/tests/test_review_gate.py`
      and observe failures.
- [x] 3.2 [req: gate-review-submission-body] In
      `plugins/s/skills/review/scripts/review_gate.py` `_post_review`, read
      the login once with `gh(["api", "user"])` (empty on failure), build the
      heading with `room_schema.speaker_heading(ROOM_AGENT, "reviewer",
      login)` prefixed `### `, and replace the old body with the heading, a
      newline, and `Semantic review: N inline comments. Full report in the
      summary comment.` (`Semantic review posted. Full report in the summary
      comment.` when there are no inline comments). Run the review gate
      tests until they pass.

## 4. Callers, docs, version

- [x] 4.1 [req: room-join-role] In `plugins/s/skills/room/SKILL.md` step 1
      and `plugins/s/harness/bodies/room.md` step 1, add: pass
      `--role author|reviewer|ci` when the user names the agent's role, and
      pass it on every join because a rejoin without it clears the role. In
      `plugins/s/integrations/copilot/room-wake.yml` change the join line to
      `room join "$PR_NUMBER" --harness copilot-cli --role ci`.
- [x] 4.2 [req: room-poster-identity] In `docs/pr-room.md`, add two sentences:
      every agent comment opens with `☕ shipd · agent · role (for @login)`
      and `join --role` sets the role. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr-room.md`
      and confirm exit 0 and 150 lines or fewer.
- [x] 4.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      one patch above `main`'s value at build time.
- [x] 4.4 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests`, `python3 -B -m unittest discover -s
      plugins/s/skills/review/tests`, and `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests`; confirm each reports OK.
