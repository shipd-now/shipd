## MODIFIED Requirements

### Requirement: Usage counting is per-response
id: usage-dedup
base: bda255014d7a

When summing token usage from session transcripts, the aggregator SHALL count
each assistant API response exactly once at its final usage snapshot: records
are keyed by message id, and each usage field (input, output, cache write,
cache read) accumulates only the positive delta over the highest value already
counted for that id — so records repeating identical usage add nothing, and
cumulative streaming snapshots (as subagent transcripts write) sum to the
response's final value. The timing timeline SHALL still record every
timestamped record so elapsed-time attribution is unchanged.

#### Scenario: Multi-record response counts once
- **WHEN** a transcript holds four `assistant` records sharing one message id,
  each repeating `output_tokens: 678`
- **THEN** the per-model summary adds 678 output tokens once, not 2712

#### Scenario: Cumulative snapshots count the final value
- **WHEN** a transcript holds three `assistant` records sharing one message id
  whose `output_tokens` snapshots are 1, 1, then 331
- **THEN** the per-model summary adds 331 output tokens, not 1 and not 333

#### Scenario: Every usage field follows its final snapshot
- **WHEN** two records share one message id and the later record's
  `input_tokens` and `cache_read_input_tokens` are higher than the first's
- **THEN** the per-model summary reflects the later record's values for those
  fields

#### Scenario: Distinct responses still accumulate
- **WHEN** a transcript holds two `assistant` records with different message
  ids
- **THEN** both responses' usage is summed

### Requirement: Session activity sampling
id: session-activity-sampling
base: d2e81c6d5bfd

The build-report module SHALL provide dependency-free (stdlib-only) session
activity helpers: an offset-keeping tail over a session's main transcript and
its subagent transcripts that, on each poll, re-discovers subagent files,
reads only bytes appended since the previous poll, defers a torn trailing
line until it is complete, and yields
`(start_epoch, end_epoch, output_tokens)` interval events per assistant
response, keyed by message id across polls and files (synthetic records
skipped): a response's first record yields an event carrying its output-token
snapshot, and a later record of the same response yields an event only for
the positive delta over the highest snapshot already yielded, at that
record's own timestamp — so a response's events sum exactly to its final
snapshot whether its records repeat identical usage or carry cumulative
streaming snapshots — where `end_epoch` is the record's timestamp and
`start_epoch` reaches back to the previous event's end in the same tail,
capped at 120 seconds, with a first event zero-length; a multi-session tail
that syncs a keyed set of per-session tails, adding and dropping sessions
between polls, and merges their events; and a bucketizer folding interval
events into buckets of a given size (3, 6, or 12 seconds) by distributing
each event's tokens across the buckets its span overlaps, proportional to
overlap and preserving the token total exactly, so charts render continuous
throughput and a window change re-buckets accumulated history losslessly.

#### Scenario: Only appended records are new
- **WHEN** a tail is polled, two records are appended to the main transcript,
  and it is polled again
- **THEN** the second poll yields events for exactly the two appended records

#### Scenario: A mid-run subagent transcript is picked up
- **WHEN** a new `agent-*.jsonl` appears under the session's subagents
  directory between polls
- **THEN** the next poll includes that file's response events

#### Scenario: Cumulative snapshots yield delta events
- **WHEN** a subagent transcript holds two records sharing one message id with
  `output_tokens` 1 then 104
- **THEN** the poll yields events summing 104 tokens, the delta event
  timestamped at the later record

#### Scenario: Repeated identical snapshots yield no further event
- **WHEN** records repeating one message id's unchanged usage snapshot arrive
  within a poll and again in a later poll
- **THEN** only the first record yields an event

#### Scenario: A torn line is deferred, not lost
- **WHEN** the transcript ends in a partial JSON line at poll time and the
  line is completed before the next poll
- **THEN** the first poll yields nothing for it and the next poll yields its
  event exactly once

#### Scenario: The multi-session tail follows the driving set
- **WHEN** a multi-session tail is synced to sessions A and B, polled, then
  synced to only B and a new C, and polled again
- **THEN** the second poll merges events from B and C only

#### Scenario: Tokens spread over the generation interval
- **WHEN** a tail yields a response 30 seconds after the previous one and its
  event is bucketed at 3 seconds
- **THEN** the event spans back 30 seconds and its tokens distribute across
  the overlapped buckets instead of landing in a single bucket

#### Scenario: The spread is capped
- **WHEN** a response arrives 600 seconds after the previous event
- **THEN** its interval spans only the final 120 seconds

#### Scenario: A first event lands in one bucket
- **WHEN** a tail's first-ever event is bucketed
- **THEN** its span is zero-length and all its tokens land in the bucket of
  its timestamp

#### Scenario: Re-bucketing preserves totals
- **WHEN** accumulated interval events are bucketed at 3 seconds and again at
  12 seconds
- **THEN** both bucketings sum to the same token total, exactly
