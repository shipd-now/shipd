# build-telemetry

### Requirement: Per-model token accounting from transcripts
id: per-model-token-accounting-from-transcripts

The telemetry tool SHALL compute a build's token usage by reading the current
session transcript and every subagent transcript for that session, aggregating
usage per model. It SHALL source counts from the transcript usage fields:
`input_tokens` (non-cached input), `output_tokens`, `cache_creation_input_tokens`
(cache write), and `cache_read_input_tokens` (cache read).

#### Scenario: Orchestrator and sub-agents are both counted
- **WHEN** the tool runs after a build that spawned execution sub-agents
- **THEN** the totals include usage from the orchestrator's session transcript AND
  from each subagent transcript, attributed to the correct model per record

#### Scenario: Usage is broken down per model
- **WHEN** a build uses more than one model (e.g. an orchestrator model and a
  cheaper execution model)
- **THEN** the tool can report a separate token breakdown for each model

### Requirement: Non-cached vs cached split, non-cached first
id: non-cached-vs-cached-split-non-cached-first

The tool SHALL separate non-cached tokens (`input_tokens` + `output_tokens`) from
cached tokens (`cache_creation_input_tokens` + `cache_read_input_tokens`), and
SHALL present non-cached figures before cached figures because non-cached tokens
are the expensive ones.

#### Scenario: Summary line ordering
- **WHEN** the tool prints the one-line token summary
- **THEN** it shows non-cached input (`↑`) and output (`↓`) first, followed by a
  parenthetical cache breakdown of cache-write (`↑`) and cache-read (`↓`),
  formatted like `Tokens: 603↑ 57.2k↓ (cache: 1.7K↑, 82.5M↓)`

### Requirement: Build-scoped measurement
id: build-scoped-measurement

The tool SHALL scope its counts to a single build by including only transcript
records at or after a supplied build-start timestamp. Without a timestamp it MAY
count the whole session, but the standard flow SHALL pass the build-start time.

#### Scenario: Only the current build is counted
- **WHEN** the tool is given the build's start timestamp
- **THEN** usage recorded before that timestamp (earlier builds, unrelated chat) is
  excluded from the totals

### Requirement: Robust source discovery and degradation
id: robust-source-discovery-and-degradation

The tool SHALL locate the transcript directory from the working directory without
manual configuration, and SHALL degrade gracefully — reporting what it can and
noting the shortfall — if transcripts are missing or unreadable, rather than
failing the build. When the working directory's own transcript directory does
not exist and the working directory is a linked git worktree, the tool SHALL
resolve the worktree's main checkout root from the worktree's `.git` file
(`gitdir: <main>/.git/worktrees/<name>`) without invoking git, and SHALL use
the main checkout's transcript directory instead.

#### Scenario: Transcript directory derived from the project path
- **WHEN** the tool runs inside the project with no explicit path override
- **THEN** it resolves the session transcript directory from the project path and
  selects the active session's transcript

#### Scenario: Worktree build falls back to the main checkout's transcripts
- **GIVEN** a session launched from the main checkout that runs a build inside
  `.worktrees/<change>`
- **WHEN** the tool runs from the worktree and no transcript directory exists
  for the worktree's own path slug
- **THEN** it resolves the main checkout root from the worktree's `.git` file
  and reads the session transcripts from the main checkout's slug

#### Scenario: A session launched inside the worktree is unaffected
- **WHEN** the tool runs in a directory whose own transcript directory exists
- **THEN** that directory is used and no worktree resolution is attempted

#### Scenario: Missing transcripts do not break the build
- **WHEN** the transcript files cannot be found or read
- **THEN** the tool emits a best-effort report with a clear note that token figures
  are unavailable, and exits without error

### Requirement: Per-model and total elapsed time
id: per-model-and-total-elapsed-time

The telemetry tool SHALL compute, from record timestamps, the build's total
elapsed wall-clock time and a per-model time breakdown. Total elapsed time SHALL
span from the build-start timestamp (or the first in-window record when no start
is given) to the last in-window record. The per-model breakdown SHALL partition
that elapsed time without overlap so the per-model times sum to the total, by
attributing the interval preceding each record to the model that produced that
record. Non-positive intervals (clock skew) SHALL be treated as zero.

#### Scenario: Total elapsed time is derived from timestamps
- **WHEN** the tool runs with a build-start timestamp
- **THEN** it reports the wall-clock duration from that start to the last recorded
  activity of the build

#### Scenario: Per-model times partition the total
- **WHEN** a build used more than one model
- **THEN** each model has an attributed elapsed time and the per-model times sum to
  the reported total (up to rounding)

#### Scenario: Timing degrades gracefully
- **WHEN** timestamps are missing or unreadable
- **THEN** the tool omits timing rather than failing, and the rest of the report
  and the build still complete

### Requirement: Per-model table rendering
id: per-model-table-rendering

The telemetry tool SHALL be able to render a markdown table of the per-model
breakdown — non-cached input/output and cache write/read token columns plus a time
column — with a Total row, and a total-runtime line, for inclusion in the standard
report.

#### Scenario: Table output mode
- **WHEN** the tool is asked to render the table
- **THEN** it prints a markdown table with one row per model, a Total row summing
  every column, and a line stating the total build runtime

#### Scenario: Table reflects the same figures as the summary
- **WHEN** both the one-line token summary and the table are produced for the same
  build window
- **THEN** the Total row's token figures match the summary line's figures

### Requirement: Synthetic records are excluded from telemetry
id: synthetic-records-excluded

The telemetry tool SHALL exclude transcript records whose model is the
harness marker `<synthetic>` from the per-model usage breakdown and from
elapsed-time attribution, so no pseudo-model row appears in the table and
no wall-clock time is attributed to a non-model. Records from real models
SHALL be unaffected, including any with zero usage.

#### Scenario: Synthetic records produce no table row
- **WHEN** the build window contains records from a real model and a
  `<synthetic>` record with zero usage
- **THEN** the per-model breakdown contains only the real model and no
  `<synthetic>` row

#### Scenario: Synthetic time folds into real attribution
- **WHEN** a `<synthetic>` record sits between two records of a real model
- **THEN** the per-model times still sum to the reported total and none is
  attributed to `<synthetic>`

#### Scenario: Zero-usage real records stay visible
- **WHEN** a record from a real model reports zero tokens in the window
- **THEN** that model still appears in the breakdown
