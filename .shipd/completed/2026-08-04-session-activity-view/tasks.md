## 1. Usage dedup fix

- [x] 1.1 [req: usage-dedup] In
      `plugins/s/skills/build/tests/test_build_report.py`, add a failing test:
      a transcript fixture holding four `assistant` records sharing one
      `message.id` (identical usage) plus one record with a distinct id;
      assert `summarize_usage` sums the shared response once and the distinct
      one once, and that the returned timeline still holds five entries. Run
      it and observe it fail.
- [x] 1.2 [req: usage-dedup] In
      `plugins/s/skills/build/scripts/build_report.py`, dedupe usage
      accumulation in `summarize_usage` by `message.id` (seen-id set; records
      with no id keep current behavior), leaving `timeline` appends
      per-record; confirm the 1.1 test passes.

## 2. Activity data helpers

- [x] 2.1 [req: session-activity-sampling] In
      `plugins/s/skills/build/tests/test_build_report.py`, add failing tests
      for `ActivityTail.poll()`: appended-records-only across two polls, a
      torn trailing line deferred then yielded once, a subagent
      `agent-*.jsonl` created between polls picked up, cross-poll message-id
      dedup, and synthetic-model records skipped.
- [x] 2.2 [req: session-activity-sampling] In
      `plugins/s/skills/build/scripts/build_report.py`, implement
      `ActivityTail` (per-file byte offsets, rewind to last newline, subagent
      re-discovery via `subagent_transcripts`, per-message dedup, yields
      `(epoch_seconds, output_tokens)`); confirm the 2.1 tests pass.
- [x] 2.3 [req: session-activity-sampling] In
      `plugins/s/skills/build/tests/test_build_report.py`, add failing tests
      for `MultiTail` (sync to sessions A+B, poll, sync to B+C, poll — second
      poll merges B and C only) and `bucket_events` (3s vs 12s bucketings of
      the same events sum to the same total).
- [x] 2.4 [req: session-activity-sampling] In
      `plugins/s/skills/build/scripts/build_report.py`, implement `MultiTail`
      (keyed tails, `sync(keys)` adds/drops, `poll()` merges) and
      `bucket_events(events, bucket_seconds)`; confirm the 2.3 tests pass.

## 3. Chart rendering helpers

- [x] 3.1 [req: block-chart-rendering] In
      `plugins/s/skills/build/tests/test_build_report.py`, add failing tests
      for `render_chart(series, rows, floor, ceiling)` (3 strings at 3 rows;
      ceiling column all `█`; floor column blank; intermediate column tops in
      a partial eighth-block; 1-row form), `scale_bounds` (auto: min 4000 /
      peak 10000 → floor 3000, ceiling `ceil(11000/500)*500`; fixed →
      `(0, 12000)`; all-zero series safe), and `fmt_tokens` (678 → `678`,
      5600 → `5.6K`).
- [x] 3.2 [req: block-chart-rendering] In
      `plugins/s/skills/build/scripts/build_report.py`, implement
      `render_chart` (cell fill `clamp(frac*rows - (rows-1-r))`, char index
      `ceil(fill*8)` into `▁▂▃▄▅▆▇█`, blank at 0), `scale_bounds`, and
      `fmt_tokens`; confirm the 3.1 tests pass.

## 4. Header throughput chart

- [x] 4.1 [req: board-throughput-chart] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: with a driving heartbeat entry and a transcript fixture, the
      header chart widget renders non-blank eighth-block cells and its label
      text carries the newest bucket value; with no driving members it
      renders blank without error; clicking it pushes the graph config
      dialog screen.
- [x] 4.2 [req: board-throughput-chart] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the header
      chart widget in the controls strip: app chart state
      `{bucket_seconds: 3, rows: 3, scale: "auto"}`, a `MultiTail` synced
      each 3-second interval tick to the driving members whose transcripts
      resolve (explicit session id, else newest for the member's location),
      raw-event accumulation, render via `bucket_events`/`scale_bounds`/
      `render_chart` at 15 columns with the 3-row label column (peak /
      window label / now) or 1-row sparkline form, and `on_click` pushing the
      config dialog; confirm the 4.1 tests pass.

## 5. Graph config dialog

- [x] 5.1 [req: graph-config-dialog] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: the dialog shows three setting rows; arrow keys move the row
      selection and change the window to `90s` (app state records 6-second
      buckets); switching height to `1 row` makes the header render its
      sparkline form while the dialog chart stays 3 rows; `esc` dismisses.
- [x] 5.2 [req: graph-config-dialog] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the
      `GraphConfigScreen` modal: width-adaptive 3-row chart with
      peak/window/now detail, three segmented rows (window / height / scale)
      with `↑`/`↓`/`←`/`→` bindings and clickable options mutating the app
      chart state, `esc` close; confirm the 5.1 tests pass.

## 6. Member modal activity panel

- [x] 6.1 [req: session-activity-timeline] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: a `MemberDetailScreen` for a member with a session id and an
      on-disk transcript fixture mounts an activity panel whose text contains
      eighth-block characters and a detail line with the session total; a
      member with no session id and no driving entry mounts no panel; after
      appending records to the transcript, invoking the screen's refresh
      handler updates the panel text.
- [x] 6.2 [req: session-activity-timeline] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the panel in
      `MemberDetailScreen`: resolve the member's session (explicit id first,
      else newest transcript while the entry state is `driving`, else no
      panel), mount a width-adaptive 3-row chart plus detail line (peak, now,
      window, session total) between header and tabs, refresh with
      `set_interval(3.0)` polling its own `ActivityTail` and re-bucketing per
      the app chart state; confirm the 6.1 tests pass.

## 7. Ship

- [x] 7.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 7.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` in an environment without `textual`, and
      the `tests_textual` suite with it installed; both suites pass.
