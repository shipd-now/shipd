## MODIFIED Requirements

### Requirement: Standard end-of-build report
id: standard-end-of-build-report
base: 45c5a68f9fa6

Every `/s:build` run SHALL end with a report in this fixed structure and order:

1. A token summary line beginning `Build complete. Tokens:` followed by the
   non-cached-first token summary.
2. A change-set header line: `Change: <name> — <done>/<total> tasks,
   Status: <status>`. The line SHALL NOT carry a schema or workflow label: the
   only value ever written was a constant, so it distinguished nothing while
   reading as though it did.
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

Where the resolved pipeline's `build` entry declares `telemetry` false, the
report SHALL omit its token blocks — item 1's token summary (the first line
reads `Build complete.` followed by the summary sentence), the per-model
table, and the total-runtime line — and SHALL keep every other item in
order; the persistent build log remains best-effort and unaffected.

#### Scenario: The change header carries no schema label
- **WHEN** the change-set header line is rendered
- **THEN** it names the change, the task counts, and the status, and carries no
  parenthesised schema or workflow label

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

#### Scenario: Telemetry opt-out drops only the token blocks
- **GIVEN** a resolved build entry declaring `telemetry` false
- **WHEN** the build finishes
- **THEN** the report carries no token summary, per-model table, or
  total-runtime line, while the change header, any warnings, the
  description with the commit hash, and Observations still print in order

### Requirement: Persistent build log
id: persistent-build-log
base: f3f49a184ebc

Each completed build SHALL be recorded under the resolved build log
directory — default `~/.shipd/builds/` — as a structured entry capturing at
least: timestamp, change name, task counts, status, commit hash, the
per-model token breakdown (non-cached and cached), the per-model time
breakdown, and the total build runtime. The entry SHALL NOT carry a schema or
workflow label, and the reporter SHALL NOT accept an option for one. Entries
written before that field was retired keep it; nothing reads it, so the log is
heterogeneous by design rather than migrated. The directory SHALL be created on
demand. Logging failures SHALL NOT fail the build. No path under
`~/.shipd/` SHALL be read or written.

#### Scenario: A build appends a log entry
- **WHEN** a build completes under default configuration
- **THEN** a structured record for it exists under `~/.shipd/builds/`
  containing the change name, commit hash, status, per-model token and time
  breakdowns, and total runtime

#### Scenario: The appended entry carries no schema key
- **WHEN** a build appends its log entry
- **THEN** that entry has no `schema` key at all — not the key with a null
  value

#### Scenario: The reporter rejects a schema option
- **WHEN** the reporter is invoked with a `--schema` option
- **THEN** it exits non-zero reporting the option as unrecognized, rather than
  accepting and ignoring it

#### Scenario: The log directory is created on demand
- **WHEN** `~/.shipd/builds/` does not yet exist at build time
- **THEN** it is created automatically before the entry is written
