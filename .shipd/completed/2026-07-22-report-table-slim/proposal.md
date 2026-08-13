# report-table-slim
Status: verified

## Why

The per-model report table carries six data columns; the cache figures
(Cache ↑ / Cache ↓) duplicate what the summary line already shows in
aggregate, and Time % adds little next to the absolute Time column. Meanwhile
there is no at-a-glance share of the actual work tokens. The table should get
slimmer and more informative: drop the cache columns and Time %, add a
Token % share right after Tokens ↓.

## What Changes

- The report table columns become: `Model | Tokens ↑ | Tokens ↓ | Token % |
  Time` — cache columns and Time % removed.
- `Token %` is the model's share of the build's total non-cached output
  tokens (Tokens ↓), whole percents; the Total row reads 100%.
- The summary line (which includes the aggregate cache figures) and the
  `Total time:` line are unchanged; the persisted log entry keeps the full
  per-model breakdown including cached counts.
- A unit test for the table renderer is added (it had none).

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `build-reporting`: the standard-report requirement's table clause changes to
  the new column set.

## Impact

- Modified: `plugins/s/skills/build/scripts/build_report.py`
  (`render_table`).
- New: `plugins/s/skills/build/tests/test_build_report.py`.
- No changes to SKILL.md (its TABLE description is column-agnostic), the log
  format, or the summary line.
