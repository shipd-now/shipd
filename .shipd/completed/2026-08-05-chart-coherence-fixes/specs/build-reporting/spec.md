## MODIFIED Requirements

### Requirement: Session activity sampling
id: session-activity-sampling
base: 9dc0e7745b3c

The build-report module SHALL provide dependency-free (stdlib-only) session
activity helpers: an offset-keeping tail over a session's main transcript and
its subagent transcripts that, on each poll, re-discovers subagent files,
reads only bytes appended since the previous poll, defers a torn trailing
line until it is complete, and yields one
`(start_epoch, end_epoch, output_tokens)` interval event per assistant
response (deduped by message id across polls and files, synthetic records
skipped) — where `end_epoch` is the response's timestamp and `start_epoch`
reaches back to the previous event's end in the same tail, capped at 120
seconds, with a first event zero-length; a multi-session tail that syncs a
keyed set of per-session tails, adding and dropping sessions between polls,
and merges their events; and a bucketizer folding interval events into
buckets of a given size (3, 6, or 12 seconds) by distributing each event's
tokens across the buckets its span overlaps, proportional to overlap and
preserving the token total exactly, so charts render continuous throughput
and a window change re-buckets accumulated history losslessly.

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
