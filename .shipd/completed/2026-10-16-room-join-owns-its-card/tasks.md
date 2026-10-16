## 1. Join owns only its own card

- [x] 1.1 [req: room-join-verb] In
      `plugins/s/skills/room/tests/test_room.py`, in `JoinTest`, add tests
      with `FakeGh`: (a) PR 14 holds issue comment 6206725970 whose body is a
      `shipd-room-card` marker naming `semantic-review`, the line
      `<!-- shipd-semantic-review -->`, and summary prose; `join 14 --agent
      semantic-review` records no PATCH and no DELETE, exactly one POST whose
      first line is a `shipd-room-card` marker naming `semantic-review`, the
      printed `comment` is the new comment's id, and comment 6206725970's body
      is byte-for-byte unchanged; (b) a second `join` then records one PATCH
      on the new comment and none on 6206725970; (c) the same as (a) with the
      legacy `<!-- am-semantic-review -->` marker; (d) a comment holding a
      card for `codex-a` plus a second room marker (a `shipd-room` Message)
      is not owned, so `join --agent codex-a` POSTs and does not PATCH; (e) a
      card for `codex-a` inside a foreign comment and an earlier owned card
      comment for `codex-a`: `join` PATCHes the owned one. Run
      `python3 -B -m unittest plugins/s/skills/room/tests/test_room.py` and
      observe (a), (c), and (d) fail.
- [x] 1.2 [req: room-join-verb] In `plugins/s/skills/room/scripts/room.py`,
      add `_owned_card_ids(comments)` returning a dict of card name to the id
      of the last issue-endpoint comment (by the order `_read_comments`
      returns) that parses to exactly one room marker, an `AgentCard`, and
      whose body contains neither `<!-- shipd-semantic-review -->` nor
      `<!-- am-semantic-review -->`; a comment whose marker does not parse is
      skipped. Use `room_schema.parse_comments` for the marker count. In
      `cmd_join`, replace the `raw` lookup with `_owned_card_ids(comments)`
      (use the `comments` element `_read_room` already returns), PATCH only
      the owned id, else POST. Leave `_parse_room`'s `raw` unchanged so no
      other verb is affected. Update the module docstring's `join` line to
      say it refreshes this agent's own card comment. Run `test_room.py`
      until it passes.

## 2. Docs and version

- [x] 2.1 [req: room-join-verb] In `docs/pr-room.md`, where `join` is
      described, add one sentence: `join` edits only the card comment it
      posted, and posts its own card even when the agent's card also appears
      inside the review summary. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr-room.md`
      and confirm exit 0 and 150 lines or fewer.
- [x] 2.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      one patch above `main`'s value at build time.
- [x] 2.3 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/room/tests` and `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests`, and confirm both report OK.
