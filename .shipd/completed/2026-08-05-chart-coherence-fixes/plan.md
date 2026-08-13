# chart-coherence-fixes
Status: verified

## Idea

Make the live activity charts read as continuous throughput and make the graph
config dialog usable — three defects found on first real use of
`session-activity-view`.

### Motivation

On a real board the charts render isolated blips because each API response's
tokens land in the single 3-second bucket at its completion timestamp, and the
config dialog is effectively unusable: each setting row shows only its first
option (full-width stretch), there is no ✕ close control, and repeated clicks
on the header chart stack identical modals so Escape appears not to work.

### Details

- Spread each response's tokens across the interval it was generated over
  (previous event → completion, capped), so charts render continuous
  throughput instead of isolated spikes.
- Fix the dialog's setting rows so every option is visible and clickable.
- Add a ✕ close control, guard the header chart against stacking a second
  dialog, and make the Escape binding priority.

Affected capabilities: `build-reporting` (modified), `delivery-dashboard`
(modified). Impact: `plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No visual restyle of the dialog beyond the option-row fix — the Shipd
  restyle belongs to the `update-ui-look-feel` epic's `board-modals` member.
- No new metrics, windows, or scale modes; no config persistence.
- No changes to `aggregate()`/usage dedup or the timing timeline.

## Implementation

- **Interval events.** `ActivityTail.poll()` yields
  `(start_epoch, end_epoch, output_tokens)` per response: `end` is the
  response's timestamp; `start = end - min(end - prev_end, 120)` where
  `prev_end` is the previous event's end **in the same tail** (first event:
  `start == end`). The 120s cap stops a long idle gap smearing tokens back
  through time. Rejected: spreading in the widget — every consumer
  (header, dialog, modal) would duplicate it.
- **Proportional bucketing.** `bucket_events(events, bucket_seconds)` accepts
  the interval triples and distributes each event's tokens over the buckets
  its `[start, end]` span overlaps, proportional to overlap length (a
  zero-length span lands wholly in its bucket). Distribution preserves the
  token total exactly (remainder assigned to the last bucket), so the
  re-bucketing invariant holds unchanged.
- **Callers unchanged in shape**: `MultiTail.poll()` merges the same triples;
  `chart_lines_and_stats` and the widgets keep consuming
  `bucket_events` output — only the event tuple widens, so accumulated-event
  lists in the widgets carry triples now.
- **Option row fix**: `.graph-option { width: auto; height: 1; }` — the
  default 100% width is what pushed sibling options off-screen.
- **Close control**: a ✕ `Button` (`compact-button` class, top-right, id
  `graph-config-close`) mirroring `MemberDetailScreen`'s pattern; its handler
  dismisses.
- **Stack guard**: `HeaderChart.on_click` returns without pushing when
  `isinstance(self.app.screen, GraphConfigScreen)` — at most one dialog ever.
- **Escape priority**: the dialog's escape `Binding` gains `priority=True` so
  it fires regardless of focus location.
- **Risk**: proportional distribution must not drift totals under float
  division — guarded by integer remainder assignment and the existing
  re-bucketing-preserves-totals scenario, extended to spread events.
