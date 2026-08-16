# board-review-lane
Status: verified

## Idea

Make the delivery board's lane resolution honor a live interactive build
heartbeat, so a member whose `/s:build` session is in its review stage renders
in the `review` lane instead of jumping straight to `shipped`.

### Motivation

An interactive `/s:build` records its stages in the build heartbeat, but the
board's lane resolver (`_member_column`) reads only the autopilot roster entry —
so once the build stage archives the change, the member maps to `shipped` while
its review stage is still running, and the `review` lane always shows
`nothing in review` for interactive builds.

### Details

- Extend `_member_column`/`_lane_contents` in
  `plugins/s/skills/build/scripts/dashboard.py` to consult the member's
  attached `build_heartbeat`: while it is live (per the existing
  `_build_is_live` predicate), place the card in `review` when its stage is
  `review`, else in `building` — overriding the lifecycle-state mapping.
- Append the live build stage to the lane card's row text
  (`TaskCard._card_text`) and show the `stage:` chip in the spec-detail modal
  (`MemberDetailScreen.compose`), mirroring the roster-driven rendering.
- Bump the plugin version in `plugins/s/.claude-plugin/plugin.json`.

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_board_activity.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No changes to the heartbeat writers (`heartbeat.py` verbs) or the autopilot
  roster semantics — only the board-side reading changes.
- No changes to the header activity indicator or throughput chart — they
  already read the build heartbeat correctly.
- No new staleness UI for build-heartbeat cards — an aged-out heartbeat simply
  falls back to the existing state mapping (no dagger/stale treatment, which
  remains autopilot-roster-only).

## Implementation

- **Hook point: `_member_column(member, entry, dead=False, now=None)`**
  (`dashboard.py:753`). Insert the build-heartbeat branch *after* the roster
  `driving` check and *before* the shipped/archived mapping: when
  `_build_is_live(member.get("build_heartbeat"), now)`, return `"review"` if
  the heartbeat's `stage` is `review`, else `"building"`. `_lane_contents`
  passes its `now` through. Rejected: synthesizing a fake roster entry in
  `_lane_contents` — it would leak into `member_signal` and the modal's
  entry-based rendering, which must stay roster-driven.
- **Precedence order (binding):** roster `driving` entry > live build
  heartbeat > `shipped`/`archived` > parked (`rejected`/`needs-human`) > plain
  state mapping. The roster wins so autopilot-driven boards are byte-identical
  to today; the build heartbeat wins over `archived` because the interactive
  build archives the change before its review stage runs — that is the bug.
- **Stage→lane mapping mirrors autopilot:** only stage `review` maps to the
  `review` lane; every other stage (`implement`, `verify`, `merge`) maps to
  `building`, matching the roster mapping at `dashboard.py:768`. Rejected:
  also mapping `merge` to `review` — no autopilot precedent, and the merge
  stage is seconds long.
- **Liveness is the existing predicate, unchanged:** `_build_is_live`
  (`dashboard.py:584`; state `running`, liveness stamp within
  `BUILD_FRESH_SECONDS` = 600s, transcript-mtime aware). A killed session ages
  out and the card falls back to its state lane automatically; `build-finish`
  sets state `finished`, which is not live, so a completed build lands in
  `shipped` immediately.
- **Card and modal stage display:** `TaskCard._card_text`
  (`dashboard.py:2555`) appends `[$fg-muted] · <stage>[/]` for a live build
  heartbeat exactly as it does for a roster-driving entry; the shipped-glyph
  early return already routes through `_member_column`, so it needs no
  change. `MemberDetailScreen.compose` (`dashboard.py:1858`) adds the muted
  `stage: <stage>` chip when the member carries a live build heartbeat and no
  roster stage chip or parked signal applies; the lane badge already calls
  `_member_column`, so it corrects itself for free.
- **Tests:** stdlib lane tests extend `tests/test_board_activity.py`'s
  `_lane_contents(board, now=...)` pattern (fixed `now`, heartbeats as plain
  dicts). Card/modal rendering tests live in `tests_textual/test_dashboard.py`
  (requires `pip install -r requirements.txt`). Verified premise: from
  `plugins/s/skills/build`, `python3 -m unittest discover -s tests` currently
  reports `Ran 1152 tests … OK`.

Risk: a stale `running` heartbeat inside the 600s window keeps a genuinely
finished member out of `shipped` for up to 10 minutes; accepted — the same
window already governs the header's `building` marker, so the board stays
internally consistent.
