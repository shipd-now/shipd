# build-reporting

### Requirement: Standard end-of-build report
id: standard-end-of-build-report

Every `/s:build` run SHALL end with a report in this fixed structure and order:

1. A token summary line beginning `Build complete. Tokens:` followed by the
   non-cached-first token summary.
2. A change-set header line: `Change: <name> (schema: <schema>) — <done>/<total>
   tasks, Status: <status>`.
3. A **spec-merge warnings** line: when the merge engine reported any warnings
   (stale base-hash overwrite, id collision, missing target), one line per
   warning prefixed `⚠ spec:` naming the requirement `id` and the warning kind.
   When the merge produced no warnings, this block is omitted entirely.
4. A **per-model breakdown table** (markdown) with one row per model used in
   the build and these columns in order: the model, its non-cached input
   tokens, its non-cached output tokens, a **Token %** column giving that
   model's share of the build's total non-cached output tokens, and a **Time**
   column giving how long that model was responsible for. Cache token counts
   and a time-share percentage SHALL NOT appear as table columns. The table
   SHALL end with a **Total** row aggregating every column, whose Token %
   reads 100%.
5. A **total runtime** line at the bottom of the table stating the build's overall
   wall-clock duration.
6. A short prose paragraph describing what was built, which SHALL include the
   commit hash.
7. An `Observations` section listing anything the user can act on or find
   interesting; when there is genuinely nothing, it SHALL say `nothing to note`.

#### Scenario: Report shape
- **WHEN** a build finishes
- **THEN** the orchestrator prints the token line, then the change header, then
  any spec-merge warning lines, then the per-model table (with a Total row), then
  the total-runtime line, then the description paragraph including the commit
  hash, then Observations — in that order

#### Scenario: Merge warnings are first-class
- **WHEN** the merge engine's summary contains a stale base-hash warning for
  requirement `enforce-sso-timeout`
- **THEN** the report shows a `⚠ spec:` line naming `enforce-sso-timeout` and
  the warning kind, above the per-model table — not buried in Observations or a
  log

#### Scenario: Clean merges stay quiet
- **WHEN** the merge produced no warnings
- **THEN** no warnings block appears in the report

#### Scenario: Table shows tokens, token share, and time
- **WHEN** a build used more than one model
- **THEN** each row shows the model's non-cached input and output tokens, a
  Token % equal to its share of total output tokens, and its Time; no cache
  columns or Time % appear; and the Total row aggregates every column with
  Token % at 100%

#### Scenario: Total runtime is shown
- **WHEN** a build finishes
- **THEN** the report states the total wall-clock time the build took to run

#### Scenario: Empty observations are explicit
- **WHEN** there is nothing actionable or interesting to surface
- **THEN** the Observations section reads `nothing to note` rather than being
  omitted or padded

### Requirement: Persistent build log
id: persistent-build-log

Each completed build SHALL be recorded under the resolved build log
directory — default `~/.shipd/builds/` — as a structured entry capturing at
least: timestamp, change name, schema, task counts, status, commit hash, the
per-model token breakdown (non-cached and cached), the per-model time
breakdown, and the total build runtime. The directory SHALL be created on
demand. Logging failures SHALL NOT fail the build. No path under
`~/.shipd/` SHALL be read or written.

#### Scenario: A build appends a log entry
- **WHEN** a build completes under default configuration
- **THEN** a structured record for it exists under `~/.shipd/builds/`
  containing the change name, commit hash, status, per-model token and time
  breakdowns, and total runtime

#### Scenario: The log directory is created on demand
- **WHEN** `~/.shipd/builds/` does not yet exist at build time
- **THEN** it is created automatically before the entry is written

### Requirement: User configuration file
id: user-configuration-file

`/s:build` SHALL read optional settings from the resolved layered
configuration's `build` key — typically declared in `~/.shipd-config.json` —
applying documented defaults when no layer declares it or a key is missing.
A committed example config SHALL document the available keys.

#### Scenario: Config is optional
- **WHEN** no config layer declares a `build` key
- **THEN** the build proceeds using documented defaults

#### Scenario: Config controls logging
- **WHEN** the resolved `build` object disables logging
- **THEN** no build log entry is written and the build still succeeds

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
