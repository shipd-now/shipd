# session-activity-view
Status: verified

## Idea

Render live token-activity charts in the board TUI — a compact board-throughput
chart in the header, a graph config dialog, and a wide per-member chart in the
spec-detail modal — per the "Shipd Board TUI" Claude Design mock's chart and
config-dialog piece, and fix the transcript usage aggregator's per-response
over-count on the way.

### Motivation

A member being driven by the autopilot shows a dead-end modal with no
visibility into what its session is doing, and the board has no activity
signal at all — although session transcripts already carry timestamped
per-response token usage. Verifying that data also exposed that
`summarize_usage` counts a multi-record API response once per record,
over-counting tokens in every build report.

### Details

- Fix `summarize_usage` in `build_report.py` to count each assistant API
  response exactly once (dedupe by `message.id` across its records).
- Add stdlib helpers to `build_report.py`: an offset-keeping `ActivityTail`
  per session (main + subagent transcripts), a `MultiTail` summing several
  sessions into shared buckets, bucketing at 3/6/12-second sizes, an
  eighth-block chart renderer, and auto/fixed scale bounds.
- In `dashboard.py`: a header chart of board throughput (output tokens summed
  across every driving member's session), a click-to-open graph config dialog
  (window / height / scale), and a wide activity panel in
  `MemberDetailScreen` for the member's own session.

Affected capabilities: `build-reporting` (modified module, added
requirements), `delivery-dashboard` (added requirements). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No OpenTelemetry, no OTLP receiver, no change to how sessions are spawned.
- No mid-drive session takeover; the `open` action's `driving` guard stands.
- No metric series beyond output tokens; the mock's vestigial `gMetric` state
  is not ported.
- No persistence of chart config — in-app state only, defaults on relaunch.
- No fix to `compute_timing` semantics; only usage summation gains dedup.
- No other piece of the Shipd mock (header redesign, search, filters, rows) —
  those belong to the `update-ui-look-feel` epic's members.

## Implementation

- **Data layer in `build_report.py`** (stdlib, already owns transcript
  location). `ActivityTail(tdir, session_id)`: per-file byte offsets, rewinds
  torn trailing lines, re-discovers `subagent_transcripts` each `poll()`,
  dedupes by `message.id` across polls/files, skips synthetic records, yields
  `(epoch_seconds, output_tokens)` events. `MultiTail`: holds
  `{(tdir, session_id): ActivityTail}`, `sync(keys)` adds/drops tails as
  driving sessions come and go, `poll()` merges all events. Rejected: board
  aggregation inside `dashboard.py` — it would be untestable without textual.
- **Bucketing:** callers accumulate the raw `(epoch_seconds, output_tokens)`
  events and fold them at render time with `bucket_events(events,
  bucket_seconds)` → `{bucket_start_epoch: token_sum}`, so switching the
  window re-buckets the full accumulated history losslessly. Bucket size
  comes from the window setting: 3, 6, or 12 seconds.
- **Renderer (mock-pinned):** `render_chart(series, rows, floor, ceiling)` →
  `rows` strings using `▁▂▃▄▅▆▇█`: per cell,
  `frac = clamp((v - floor) / (ceiling - floor))`,
  `fill = clamp(frac * rows - (rows - 1 - r))`, char index `ceil(fill * 8)`,
  0 → space. `scale_bounds(series, mode)`: `auto` → floor
  `max(0, min*0.75)`, ceiling `ceil(peak*1.1/500)*500` (min 500); `fixed` →
  `(0, 12000)`. `fmt_tokens(v)` → `678` / `5.6K`. Rejected: the earlier
  `░▒▓` quarter-shade ramp — the design pins eighth-blocks.
- **Chart config is app state** on `BoardApp`: `{bucket_seconds: 3, rows: 3,
  scale: "auto"}`, shared by every chart; `rows` (3/1) governs the header
  footprint only — dialog and modal charts always render 3 rows wide-format.
- **Header chart** (`dashboard.py`): a widget in the controls strip, 15
  columns; 3-row form carries a right label column peak / window label
  (`45s`/`90s`/`3m`) / now (accent); 1-row form is the flat sparkline + now.
  Driven by its own `set_interval(3.0)`: sync `MultiTail` keys from the
  board's heartbeats (every member whose entry state is `driving` and whose
  transcript resolves — explicit session id, else newest transcript for the
  member's location), poll, fold buckets, re-render. No driving sessions →
  an all-blank chart, never an error. Click pushes the config dialog.
- **Graph config dialog**: a `ModalScreen` (mock: 64ch, accent title
  `graph · throughput`, metric `output tokens`) showing a width-adaptive
  3-row board-throughput chart with peak/window/now detail, then three
  segmented rows — window `45s/90s/3m`, height `3 rows/1 row`, scale
  `auto/fixed 12K`. `↑`/`↓` select the row, `←`/`→` change it, `esc` closes;
  options are also clickable. Changes apply immediately to app state.
- **Member modal panel** (`MemberDetailScreen`): resolves the member's own
  session (explicit id first, else newest transcript while the entry state
  is `driving`, else no panel), mounts a width-adaptive 3-row chart with a
  detail line (peak, now, window, session total) between the header and the
  tabs, refreshed by `set_interval(3.0)` polling its own `ActivityTail`. The
  window setting changes the bucket size here too. Without a transcript the
  modal renders exactly as today.
- **Width-adaptive charts** compute their column count from the widget's
  rendered width (header stays fixed at 15) and show the newest buckets.
- **Risks.** First poll of a big transcript is a one-time full read —
  acceptable at open. Transcript format is Claude Code internal; posture is
  the module's existing one: parse failures skip the line or file, never
  raise. Raw-event accumulation grows unbounded over a very long-lived
  board; at one event per API response this is thousands of small tuples per
  hour — accepted.
