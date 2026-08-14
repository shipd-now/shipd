## Context

`render_table` in `build_report.py` currently renders
`Model | Tokens ↑ | Tokens ↓ | Cache ↑ | Cache ↓ | Time | Time %` with a
Total row and a trailing `Total time:` line, degrading by dropping the Time
columns when timing is unavailable. The persisted log entry carries the full
per-model token/time breakdown independently of the table.

## Goals / Non-Goals

**Goals:**
- Slimmer table: `Model | Tokens ↑ | Tokens ↓ | Token % | Time`.
- Token % answers "who did the output work" at a glance.

**Non-Goals:**
- No changes to the summary line (aggregate cache figures live there), the
  `Total time:` line, the persisted log schema, or the `--json` output.
- No spec change to `persistent-build-log` (it keeps cached counts).

## Decisions

### D1 — Token % definition
`Token %` = the model's non-cached **output** tokens (the Tokens ↓ figure) as
a share of the build's total non-cached output tokens, rendered as a whole
percent (same rounding helper as the old Time %). The Total row shows `100%`.
When total output is zero, every row renders `0%` (no division error).
- *Why output, not input or sum:* output tokens are the work produced and the
  dominant cost driver; the column sits directly after Tokens ↓ and reads as
  its share.

### D2 — Degradation behavior unchanged in shape
Token % depends only on token data, so it is always present when the table
renders. Timing degradation keeps its existing behavior, now dropping only
the `Time` column when timing is unavailable (there is no Time % anymore).

### D3 — Tests target the renderer directly
`test_build_report.py` imports `build_report` (same sibling-import pattern as
the other tests) and asserts on `render_table` output for a two-model fixture:
exact header column set and order, per-row Token % arithmetic, Total row
100%, absence of `Cache` and `Time %` anywhere, presence of the `Total time:`
line, and the zero-output edge case. No subprocess needed.

## Risks / Trade-offs

- **Readers who relied on per-model cache figures** → still available in the
  persisted per-build JSON and `--json` output; the table is for the
  at-a-glance report.
