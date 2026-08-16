## 1. Lane resolution (stdlib suite)

- [x] 1.1 [req: board-live-build-lane] In
      `plugins/s/skills/build/tests/test_board_activity.py`, following the
      existing `_lane_contents(board, now=...)` test pattern (see the
      dead-run tests around line 429), add failing tests: (a) an `archived`
      member with `build_heartbeat` `{"state": "running", "stage": "review",
      "updated_at": now}` lands in the `review` lane and not `shipped`;
      (b) the same heartbeat at stage `implement` lands in `building`;
      (c) the same review heartbeat with `updated_at` older than
      `dashboard.BUILD_FRESH_SECONDS` lands in `shipped`; (d) a live roster
      entry `driving` at stage `build` plus a live build heartbeat at stage
      `review` lands in `building`. Run
      `python3 -m unittest tests.test_board_activity` from
      `plugins/s/skills/build` and observe the new tests fail.
- [x] 1.2 [req: board-live-build-lane] In
      `plugins/s/skills/build/scripts/dashboard.py`, extend
      `_member_column(member, entry, dead=False)` with a `now=None` parameter
      and, directly after the roster `driving` branch, return `"review"` when
      `_build_is_live(member.get("build_heartbeat"), now)` and the heartbeat's
      `stage` is `review`, else `"building"` when it is live; update
      `_lane_contents` to pass its `now` through, and update the docstrings.
      Confirm the tests from 1.1 now pass.

## 2. Card row and modal stage display (textual suite)

- [x] 2.1 [req: board-live-build-lane] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` (run
      `pip install -r requirements.txt` first), add failing tests: (a)
      `TaskCard._card_text` for a member with an empty roster entry and a live
      build heartbeat at stage `review` appends `· review` in the muted tier
      after the slug; (b) the `MemberDetailScreen` badge row for that member
      carries a `stage: review` chip and a `review` lane badge. Run
      `python3 -m unittest tests_textual.test_dashboard` from
      `plugins/s/skills/build` and observe them fail.
- [x] 2.2 [req: board-live-build-lane] In
      `plugins/s/skills/build/scripts/dashboard.py`, extend
      `TaskCard._card_text` (line ~2555) to append the build heartbeat's stage
      in the muted tier when `_build_is_live(self.member.get(
      "build_heartbeat"))` and no roster `driving` stage was appended, and
      extend `MemberDetailScreen.compose`'s badge row (line ~1858) to yield
      the muted `stage: <stage>` chip from a live build heartbeat when no
      parked signal and no roster stage chip applies. Confirm the tests from
      2.1 now pass.

## 3. Ship hygiene

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.104` to `0.6.105`
      (plugin-cache rule in `AGENTS.md`).
- [x] 3.2 [req: *] From `plugins/s/skills/build`, run
      `python3 -m unittest discover -s tests` and
      `python3 -m unittest discover -s tests_textual` and confirm both suites
      pass in full.
