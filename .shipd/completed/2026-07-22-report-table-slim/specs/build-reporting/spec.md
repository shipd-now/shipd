## MODIFIED Requirements

### Requirement: Standard end-of-build report
id: standard-end-of-build-report
base: b9a8004cfabd

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
