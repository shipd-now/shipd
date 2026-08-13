# modal-progress-chrome
Status: verified

## Idea

Fix three defects in the delivery board's spec-detail modal — a ✕ close
control that overhangs the container, a missing build-elapsed / task-progress
readout, and a cramped gap before the artifact tabs — and stamp the per-member
`started_at` both heartbeats need to drive the elapsed clock.

### Motivation

On the spec-detail modal the ✕ close button pushes the accent title bar ~2
cells past the modal's right border, the activity panel shows token throughput
but no build-elapsed time or task-completion progress, and the detail line
abuts the artifact tabs with no separation — three rough edges reported from an
annotated board screenshot.

### Details

- Contain the accent title bar and its inline ✕ close control within the modal
  container so its right edge aligns with the rows below (no ~2-cell overhang).
- Add a left-aligned progress line at the top of the activity panel showing
  elapsed-since-build-start and completed-task progress (`<done>/<total>` from
  `tasks.md`).
- Insert a one-row gap between the activity detail line and the artifact tabs.
- Stamp a per-member `started_at` in both heartbeats — the run-heartbeat roster
  entry at member start, and the interactive `build-start` verb — set only when
  absent, as the elapsed clock's source.

Affected capability: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/scripts/heartbeat.py`; version bump
`plugins/s/.claude-plugin/plugin.json`; tests in
`plugins/s/skills/build/tests_textual/` and `.../tests/`. No new dependencies.

### Non-goals

- No change to the token-throughput sparkline or its peak/now/window/session
  detail line beyond adding the gap below it.
- No elapsed/task readout on the text board, the HTML board, or any non-modal
  surface.
- No change to how autopilot or the build skill drive members — only an extra
  timestamp field on their existing heartbeat writes.

## Implementation

- **Title-bar containment (item 1).** Root-cause the ✕ overhang in
  `MemberDetailScreen`'s `.modal-title-bar` geometry (likely the compact
  button's box — `width: 3; padding: 0 1` — against the container's
  `padding: 1 2`) and fix it so the bar's right edge equals the container's
  content-region right edge; pin the exact cause with a pilot measurement.
  Strengthen the chrome-containment sweep to assert the title bar's (and ✕'s)
  `region.right <= container.content_region.right`. Rejected: masking with
  `overflow-x: hidden` — hides the geometry bug instead of fixing it.
- **Progress line (item 2).** Mount a left-aligned `Static` with id
  `member-activity-progress` as the first child of the activity panel (the
  panel-top slot the bare `Rule()` occupies), above the `ActivityChart`. Its
  text is `elapsed <…> · tasks <done>/<total>`, each token omitted when its
  source is missing. Resolve elapsed from `started_at` — `self.entry` roster
  entry first, else the build heartbeat file via
  `build_heartbeat_path(location, slug)` — and tasks from
  `ss.count_tasks(location, slug)` → `(done, in_progress, total)`. Refresh it on
  the existing 3-second `_refresh_activity` tick. Rejected: appending to the
  `peak…session` line — the annotation places the readout at the top-left of the
  graph, and elapsed/tasks are build-progress, not throughput.
- **`started_at` plumbing (item 2).** In `heartbeat.py`: `_build_start` sets
  `state["started_at"] = time.time()` only when absent;
  `RunHeartbeat.member_started` sets `entry["started_at"]` only when absent —
  idempotent across restarts and stage re-attempts, so the clock reflects the
  first start. The modal computes `elapsed = now − started_at`.
- **Tab gap (item 3).** Add `margin-bottom: 1` to `#member-activity-detail` in
  `MemberDetailScreen`'s CSS, opening one blank row before `TabbedContent`.
- **Packaging.** Bump `plugins/s/.claude-plugin/plugin.json` 0.6.67 → 0.6.68 so
  the cache snapshot refreshes.

Risk: elapsed for autopilot members depends on `started_at` reaching
`self.entry` (the roster entry the modal already receives); guard by also
reading the build heartbeat file, and by omitting elapsed when neither yields a
stamp. Trade-off: `started_at` is set once and never reset, so a member
re-driven within a run shows elapsed from its original start — acceptable, it
reflects true wall-clock since the build began (a fresh autopilot run reseeds
the roster and so re-stamps).
