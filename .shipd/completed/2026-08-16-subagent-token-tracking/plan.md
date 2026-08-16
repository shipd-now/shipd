# subagent-token-tracking
Status: verified

## Idea

Count each assistant response's tokens at its final usage snapshot in
`build_report.py`'s two aggregators, so subagent streaming records no longer
undercount the board token graph or the end-of-build report.

### Motivation

Subagent transcripts (`subagents/agent-*.jsonl`) write cumulative usage
snapshots per assistant message id — the first record often carries
`output_tokens: 1` — but both token aggregators keep only the first record per
id, undercounting subagent output by ~78% across this machine's 46 real
subagent transcripts (169,728 counted of 782,723 true tokens). The board
throughput graph and the build report therefore barely register subagent work
(an 89.1k-token agent renders as single-digit buckets).

### Details

- Replace keep-first-record-per-id dedupe with per-response cumulative
  counting in `ActivityTail._event` (live chart events) and
  `aggregate` (end-of-build token table): key records by message id
  and count only the positive delta over the highest snapshot already
  counted, so a response always sums to its final snapshot.
- Main transcripts, whose duplicate records repeat the final usage
  (measured: `[955, 955, 955, 955]`), yield delta 0 on repeats — their
  totals are unchanged.

Affected capabilities: `build-reporting` (modified — `usage-dedup`,
`session-activity-sampling`). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- No changes to chart rendering, bucketing, tail offsets, torn-line deferral,
  subagent file discovery, or interval-spread semantics — the counting rule
  only.
- No changes to `dashboard.py` — its widgets consume the corrected events
  unchanged.
- No change to timing/elapsed attribution: the timeline still records every
  timestamped record.

## Implementation

- **Positive-delta emission keyed by message id.** `ActivityTail` replaces its
  `_seen_ids` set with a dict mapping message id → highest `output_tokens`
  snapshot counted so far. The first record of an id yields an event carrying
  its snapshot (as today, including a 0-token first snapshot); a later record
  of the same id yields an event only for the positive delta, timestamped at
  that record (updating `_prev_end` as any event does); an equal-or-lower
  snapshot yields nothing — today's repeat dedupe, preserved. Rejected:
  recomputing per-file totals each poll (breaks the appended-bytes-only
  offset contract) and counting a response only when it ends (a live tail
  cannot know a streamed response is finished, and the tokens must chart as
  they are generated).
- **Per-field deltas in `aggregate`.** The report aggregator replaces
  `seen_ids` with a dict mapping message id → per-field highest-counted
  values, adding the positive delta for each of `input_tokens`,
  `output_tokens`, `cache_creation_input_tokens`, and
  `cache_read_input_tokens` — cumulative snapshots move every field, not just
  output. A record with no message id still counts in full, as today. The
  timing timeline keeps appending every timestamped record. Rejected:
  output-only deltas — the report table also shows input and cache columns.
- **Delta counting is exact on real data.** Per-id snapshot sequences are
  monotonic non-decreasing in every one of the 46 real subagent transcripts
  inspected (0 violations), and repeat-pattern main transcripts sum
  identically under first-per-id and max-per-id — so positive-delta
  accumulation reproduces `sum(max per id)` exactly for both record shapes.
- **Memory profile unchanged in kind.** A per-id dict replaces a per-id set
  with the same lifecycle and bound (one entry per assistant response).
- Risk: a hypothetical non-monotonic snapshot (a later record lower than an
  earlier one) would leave the higher value counted; guarded by taking only
  positive deltas, which can never double-count and never subtracts.
- Version bump: `plugins/s/.claude-plugin/plugin.json` 0.6.106 → 0.6.107 in
  the same PR (cache-snapshot rule in `AGENTS.md`).
