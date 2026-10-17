## 1. Failing tests first

- [x] 1.1 [P1] [req: room-skill-loop, room-skill-body] In
      `plugins/s/skills/room/tests/test_room_skill.py`, change
      `test_default_card_skills_and_timeout` and
      `test_background_harness_watches` to assert `--timeout 540` is present
      and `--timeout 600` absent; add assertions that the SKILL.md text
      states the tool call's own timeout exceeds 540 seconds and names
      `600000`, that the rendered background body contains `540 seconds`,
      and a test that `plugins/s/harness/references/room.md` and
      `docs/pr-room.md` each contain `--timeout 540` and no `--timeout 600`.
      Run the suite and observe the new assertions fail.
- [x] 1.2 [P1] [req: room-list-verb] In
      `plugins/s/skills/room/tests/test_room.py` `ListTest`, add
      `test_card_line_shows_role_and_omits_unset_harness`: cards
      `claude-b` (role `author`, no harness) and `codex-a` (harness `codex`,
      no role) yield exactly the lines `claude-b  role author  skills -
      version -` and `codex-a  harness codex  skills -  version -` (two
      spaces between parts), and the output contains neither `harness -`
      nor `role -`. Observe it fail.
- [x] 1.3 [P1] [req: gate-room-summary, gate-finding-room-task] In
      `plugins/s/skills/review/tests/test_review_gate.py`, rewrite
      `RoomSummaryTest` and `RoomPostTest` to the card-only contract: the
      card line sits directly above the footer's blank separator (or is the
      last line without files); `room_schema.parse_comments` of the summary
      yields exactly one `AgentCard`; the body has no `<!-- shipd-room `
      text; delete `test_message_parses_back` and
      `test_explicit_status_state_is_carried`; `_assert_summary_markers`
      asserts one card marker and zero Message markers (count the
      `<!-- shipd-room {` prefix for Messages, since the card prefix also
      starts `<!-- shipd-room`). Update the `RoomPostTest` anchored test so
      each review comment carries one `<!-- shipd-room {` line and the
      summary none. Add a test that runs `post` with two anchored findings,
      then feeds the summary comment and the posted inline comment bodies
      (inline ones as dicts with `"_room_endpoint": "review"` and ids 2000+)
      to `room._parse_room` (import `room` from the room scripts dir already
      on `sys.path`) and asserts a `semantic-review` card and tasks only
      with the inline ids.

## 2. Timeout, card line, card-only summary

- [x] 2.1 [P2] [req: room-skill-loop] In `plugins/s/skills/room/SKILL.md`,
      replace both `--timeout 600` with `--timeout 540`, change "ten-minute
      timeout" to "nine-minute timeout", and add to step 3 the sentence:
      "Give the tool call that runs `watch` its own timeout above 540
      seconds (on Claude Code, a Bash `timeout` of `600000` ms), so the
      harness never moves the wait to the background."
- [x] 2.2 [P2] [req: room-skill-body] In `plugins/s/harness/bodies/room.md`
      step 3 and `plugins/s/harness/references/room.md`'s watch-output
      section, replace `--timeout 600` with `--timeout 540` and add one
      sentence: "The tool call that runs `watch` needs its own timeout above
      540 seconds, or the harness may move the wait to the background."
- [x] 2.3 [P2] [req: room-skill-body] In `docs/pr-room.md`, replace both
      `--timeout 600` with `--timeout 540`, and after the step 3 example add:
      "Give the tool call its own timeout above 540 seconds (on Claude Code,
      a Bash `timeout` of `600000` ms) so the wait stays in the foreground."
      Run `python3 -B plugins/s/skills/document/scripts/docs_lint.py
      docs/pr-room.md` and confirm exit 0.
- [x] 2.4 [P2] [req: room-list-verb] In
      `plugins/s/skills/room/scripts/room.py`, rewrite `_card_line(card)`
      per `plan.md` Implementation "Card line": parts `card.name`,
      `role <r>` if `card.role`, `harness <h>` if `card.harness`,
      `skills <csv or ->`, `version <v or ->`, joined with two spaces.
      Confirm `test_room.py` passes.
- [x] 2.5 [P2] [req: gate-room-summary, gate-finding-room-task] In
      `plugins/s/skills/review/scripts/review_gate.py`, delete
      `_room_summary_line` and `render_summary`'s `status_state` parameter,
      emit only `_room_card_line(room)` in the room tail, drop
      `status_state=` from the three calls in `post`, and update the
      `render_summary` docstring.
- [x] 2.6 [P2] [req: summary-earlier-reviews] In `plugins/s/skills/review/tests/test_review_gate.py`, make
      `FakeGh` stamp `updated_at` on every issue-comment POST and PATCH from
      an incrementing fixed clock (`2026-10-17T12:00:00Z`, then +1 minute
      per write). Add `EarlierReviewsTest` covering every
      `summary-earlier-reviews` scenario: first post has no `Earlier
      reviews` and one `<!-- shipd-semantic-review-head <sha> -->` line;
      fix-required then pass across two heads (set `gh.head_sha` between
      posts, with a matching `FakeGit` merge base) keeps one entry starting
      `- ❌ Fix required — `+sha[:7]; three posts list newest first with one
      block; `earlier_reviews` formats `2026-10-17T12:34:56Z` as
      `2026-10-17 12:34 UTC`; a previous body without a head line yields
      `` `unknown` ``; `earlier_reviews(None)` is `[]`. Observe failures.

## 3. Earlier reviews

- [x] 3.1 [P3] [req: summary-earlier-reviews] In `review_gate.py`, add
      `HEAD_MARKER_FMT`, `EARLIER_OPEN`, `EARLIER_CLOSE`, `_find_summary`,
      and `earlier_reviews(previous)`, add `head=None, earlier=None` to
      `render_summary` with the tail order in `plan.md` Implementation
      "Head record", make `_upsert_summary` use `_find_summary`, and wire
      `post` per "Post wiring" (one `_find_summary` before the first
      upsert; `head=sha, earlier=earlier` on all three renders). Confirm the
      whole review suite passes with `python3 -B -m unittest discover -s
      plugins/s/skills/review/tests`.

## 4. Version and verification

- [x] 4.1 [P4] [req: *] Set `plugins/s/.claude-plugin/plugin.json`
      `version` to one patch above `git show
      origin/main:plugins/s/.claude-plugin/plugin.json` (run `git fetch
      origin main` first).
- [x] 4.2 [P5] [req: *] With `__pycache__` directories removed under
      `plugins/`, run with `python3 -B -m unittest discover -s <dir>` the
      room (`plugins/s/skills/room/tests`), review
      (`plugins/s/skills/review/tests`), and build
      (`plugins/s/skills/build/tests`) suites and grep each output for `OK`
      or `FAILED`; all three must report `OK`.
