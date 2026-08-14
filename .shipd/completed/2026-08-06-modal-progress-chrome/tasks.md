## 1. Per-member start timestamps (heartbeats)

- [x] 1.1 [req: build-heartbeat-cli] Add a test under
      `plugins/s/skills/build/tests/` asserting `build-start <slug>` stamps a
      `started_at` in the build heartbeat, and that a subsequent `build-stage`
      and a repeated `build-start` leave `started_at` unchanged. Run it and
      observe it fail — no `started_at` is written yet.
- [x] 1.2 [req: build-heartbeat-cli] In
      `plugins/s/skills/build/scripts/heartbeat.py`, in `_build_start`, set
      `state["started_at"] = time.time()` only when the key is absent. Confirm
      1.1 passes.
- [x] 1.3 [req: autopilot-heartbeat] Add a test under
      `plugins/s/skills/build/tests/` asserting `RunHeartbeat.member_started`
      records a `started_at` on the roster entry once, unchanged by a following
      `stage_started` for the same member. Run it and observe it fail.
- [x] 1.4 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/heartbeat.py`, in
      `RunHeartbeat.member_started`, set `entry["started_at"] = time.time()`
      only when the entry lacks the key. Confirm 1.3 passes.

## 2. Modal progress line (elapsed + tasks)

- [x] 2.1 [req: session-activity-timeline] Add a test under
      `plugins/s/skills/build/tests_textual/` (App driven via
      `App.run_test`) asserting that a driving member whose heartbeat carries a
      `started_at` and whose `tasks.md` has 4 of 11 checkboxes done renders an
      activity-panel top progress line (id `member-activity-progress`)
      containing an elapsed token and `4/11`, and that a member with no
      `started_at` omits the elapsed token. Run it and observe it fail — the
      progress line does not exist yet. (Requires `pip install -r
      requirements.txt` for `textual`.)
- [x] 2.2 [req: session-activity-timeline] In
      `plugins/s/skills/build/scripts/dashboard.py`, in
      `MemberDetailScreen.compose`, mount a left-aligned `Static` with id
      `member-activity-progress` as the first child of the activity panel (the
      panel-top slot the bare `Rule()` occupies), above the `ActivityChart`.
- [x] 2.3 [req: session-activity-timeline] In
      `plugins/s/skills/build/scripts/dashboard.py`, add a helper on
      `MemberDetailScreen` that resolves the member's `started_at`
      (`self.entry.get("started_at")` first, else read the build heartbeat via
      `build_heartbeat_path(location, slug)`) and its task counts via
      `ss.count_tasks(location, slug)` → `(done, in_progress, total)`, and
      builds the progress text `elapsed <…> · tasks <done>/<total>`, omitting
      the elapsed token when no `started_at` resolves and the tasks token when
      `count_tasks` returns `None`.
- [x] 2.4 [req: session-activity-timeline] In
      `plugins/s/skills/build/scripts/dashboard.py`, update
      `#member-activity-progress` on the existing 3-second `_refresh_activity`
      tick (alongside the chart repaint) so the elapsed token advances without
      the modal being reopened. Confirm 2.1 passes.

## 3. Spacing before the tabs

- [x] 3.1 [req: session-activity-timeline] Add a `tests_textual` assertion that
      a one-row gap separates `#member-activity-detail` from the following
      `TabbedContent` (a nonzero region gap between them). Run it and observe it
      fail — they currently abut.
- [x] 3.2 [req: session-activity-timeline] In
      `plugins/s/skills/build/scripts/dashboard.py`, in
      `MemberDetailScreen`'s CSS, add `margin-bottom: 1` to
      `#member-activity-detail`. Confirm 3.1 passes.

## 4. Title-bar containment (close button)

- [x] 4.1 [req: modal-chrome-containment] Extend the chrome-containment sweep in
      `plugins/s/skills/build/tests_textual/` to assert, for all four modal
      screens, that the accent title bar's and the `✕` close control's
      `region.right <= container.content_region.right`. Run the sweep and confirm
      it passes — the region-containment invariant is now guarded going forward.
- [x] 4.2 [req: modal-chrome-containment] Guard the historical overhang's root
      cause — a close glyph whose East-Asian width is ambiguous/wide (e.g.
      `×` U+00D7) renders two cells in ambiguous-as-wide terminals and desyncs
      the accent bar's right edge past the border, an overhang region
      measurement cannot see. Add a test (stdlib `tests/` is fine — no textual
      needed) asserting every board modal's close-control label glyph has
      `unicodedata.east_asian_width` in `{'N','Na','H'}` (never `'A'/'W'/'F'`);
      confirm the current `✕` U+2715 (width `N`) passes. No geometry change: a
      40–200 width pilot sweep shows the `MemberDetailScreen` title bar already
      contained (right edge == content-region right), so 4.1's region guard plus
      this glyph guard together lock the invariant the #158 chrome work restored.

## 5. Packaging & verification

- [x] 5.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.67` to `0.6.68`.
- [x] 5.2 [req: *] Run `pip install -r requirements.txt`, then both suites —
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and the
      `tests_textual` suite — and confirm both are green.
