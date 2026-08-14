## 1. Interval events and proportional bucketing

- [x] 1.1 [req: session-activity-sampling] In
      `plugins/s/skills/build/tests/test_build_report.py`, update/add failing
      tests: `ActivityTail.poll()` yields `(start, end, tokens)` triples where
      a response 30s after the previous spans back 30s, a 600s gap caps the
      span at 120s, and a first event is zero-length; `bucket_events` at 3s
      distributes a spanning event's tokens proportionally across overlapped
      buckets, a zero-length event lands wholly in its bucket, and 3s vs 12s
      bucketings of the same events sum to identical totals exactly. Adapt the
      existing appended-only / torn-line / subagent / MultiTail tests to the
      triple shape.
- [x] 1.2 [req: session-activity-sampling] In
      `plugins/s/skills/build/scripts/build_report.py`, implement the
      interval-event change: `ActivityTail` tracks the previous event end per
      tail and yields `(start, end, tokens)` (cap 120s, first event
      zero-length); `bucket_events` distributes tokens across overlapped
      buckets proportional to overlap with integer remainder assigned to the
      last bucket. Confirm the 1.1 tests pass.
- [x] 1.3 [req: session-activity-sampling] In
      `plugins/s/skills/build/scripts/dashboard.py`, adapt the event
      consumers (`HeaderChart`, `ActivityChart` providers,
      `chart_lines_and_stats`, `MemberDetailScreen._refresh_activity`) to the
      triple shape — accumulation and session-total math use the token field;
      run the existing `tests_textual` chart tests and fix any shape breaks.

## 2. Dialog usability fixes

- [x] 2.1 [req: graph-config-dialog] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: every setting row shows all its options each with a non-empty
      region and clicking `3m` sets `bucket_seconds` to 12; clicking the `✕`
      (`#graph-config-close`) dismisses the dialog; clicking the header chart
      twice leaves exactly one `GraphConfigScreen` on the stack and one
      `escape` returns to the board.
- [x] 2.2 [req: graph-config-dialog] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the fixes:
      `.graph-option { width: auto; height: 1; }`; a `✕` close `Button`
      (`compact-button`, id `graph-config-close`) top-right in the dialog
      whose press dismisses; `HeaderChart.on_click` returns without pushing
      when the current screen is already a `GraphConfigScreen`; the escape
      `Binding` gains `priority=True`. Confirm the 2.1 tests pass.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
