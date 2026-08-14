## ADDED Requirements

### Requirement: Usage counting is per-response
id: usage-dedup

When summing token usage from session transcripts, the aggregator SHALL count
each assistant API response exactly once, keyed by its message id, even when
the response spans multiple transcript records repeating the same usage; the
timing timeline SHALL still record every timestamped record so elapsed-time
attribution is unchanged.

#### Scenario: Multi-record response counts once
- **WHEN** a transcript holds four `assistant` records sharing one message id,
  each repeating `output_tokens: 678`
- **THEN** the per-model summary adds 678 output tokens once, not 2712

#### Scenario: Distinct responses still accumulate
- **WHEN** a transcript holds two `assistant` records with different message
  ids
- **THEN** both responses' usage is summed

### Requirement: Session activity sampling
id: session-activity-sampling

The build-report module SHALL provide dependency-free (stdlib-only) activity
helpers: a per-session offset-keeping tail over a session's main transcript
and its subagent transcripts that, on each poll, re-discovers subagent files,
reads only bytes appended since the previous poll, defers a torn trailing
line until complete, and yields one `(epoch_seconds, output_tokens)` event
per assistant response (deduped by message id across polls and files,
synthetic records skipped); a multi-session tail that syncs a keyed set of
per-session tails, adding and dropping sessions between polls, and merges
their events; and a bucketizer folding raw events into buckets of a given
size (3, 6, or 12 seconds) so a window change re-buckets accumulated history.

#### Scenario: Only appended records are new
- **WHEN** a tail is polled, two records are appended to the main transcript,
  and it is polled again
- **THEN** the second poll yields events for exactly the two appended records

#### Scenario: A mid-run subagent transcript is picked up
- **WHEN** a new `agent-*.jsonl` appears under the session's subagents
  directory between polls
- **THEN** the next poll includes that file's response events

#### Scenario: A torn line is deferred, not lost
- **WHEN** the transcript ends in a partial JSON line at poll time and the
  line is completed before the next poll
- **THEN** the first poll yields nothing for it and the next poll yields its
  event exactly once

#### Scenario: The multi-session tail follows the driving set
- **WHEN** a multi-session tail is synced to sessions A and B, polled, then
  synced to only B and a new C, and polled again
- **THEN** the second poll merges events from B and C only

#### Scenario: Re-bucketing preserves totals
- **WHEN** accumulated events are bucketed at 3 seconds and again at 12
  seconds
- **THEN** both bucketings sum to the same token total

### Requirement: Block chart rendering
id: block-chart-rendering

The build-report module SHALL provide a pure chart renderer that draws a
numeric series as `rows` strings (1 or 3 rows) of eighth-block characters
(`▁▂▃▄▅▆▇█`), computing each cell's fill from the value's fraction between a
floor and a ceiling and quantizing it to 8 levels per row (blank below the
floor); a scale-bounds helper where `auto` yields floor `max(0, min*0.75)`
and ceiling `peak*1.1` rounded up to the next 500 (minimum 500), and `fixed`
yields `(0, 12000)`; and a token formatter rendering values under 1000 as-is
and above as a `5.6K` style string.

#### Scenario: Renderer fills within its rows
- **WHEN** a series holding the floor value, the ceiling value, and an
  intermediate value is rendered at 3 rows
- **THEN** the renderer returns 3 strings in which the ceiling column is a
  full-height bar of `█`, the floor column is blank, and the intermediate
  column tops out in a partial eighth-block

#### Scenario: Auto scale clips the baseline
- **WHEN** auto bounds are computed for a series with minimum 4000 and peak
  10000
- **THEN** the floor is 3000 and the ceiling is `ceil(11000/500)*500`

#### Scenario: Helpers import without textual
- **WHEN** the tail, bucketizer, renderer, and scale helpers are exercised in
  an environment without `textual` installed
- **THEN** they work unchanged
