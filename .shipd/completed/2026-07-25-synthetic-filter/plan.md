# synthetic-filter
Status: verified
Profile: lite
Theme: developer-experience

## Idea

Build reports can show a `<synthetic>` row in the per-model table. Claude
Code writes harness-generated assistant records (model literally
`"<synthetic>"`, all-zero usage, e.g. "No response requested.") into the
transcript with real timestamps, so `build_report.py`'s timing attribution
assigns the interval before each one to a pseudo-model. The row is always
0-token noise that misreads as a model doing work.

This change filters synthetic records out of telemetry:

- `aggregate()` in `build_report.py` skips records whose `model` is
  `"<synthetic>"` — they enter neither the per-model usage map nor the
  timing timeline, so their preceding interval folds into the next real
  record's attribution and no pseudo-model row renders.
- Tests pin the behavior; plugin version bump (0.2.5 → 0.2.6, resolved
  upward at merge if main has moved).

### Non-goals

- No filtering of other zero-usage records — only the exact
  `"<synthetic>"` model marker; a real model with a zero-usage record stays
  visible.
- No backfill of logged entries in `~/.shipd/builds.jsonl`.

Affected capabilities: `build-telemetry` (modified via one ADDED
requirement). Impact: `plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/tests/test_build_report.py`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Filter at the record loop in `aggregate()`** (around
  `build_report.py:213`): after reading `message.get("model")`, skip the
  record when it equals the module constant `SYNTHETIC_MODEL =
  "<synthetic>"` — before usage accumulation and before
  `timeline.append`. One filter point covers both the table row and the
  time attribution. Rejected: post-filtering `by_model` in the renderers —
  it would leave the timeline attributing time to a dropped model, making
  per-model times no longer sum to the total.
- **Total-time consequence, accepted:** if the last in-window record is
  synthetic, total elapsed now ends at the last *real* record — more
  honest, since no model was doing anything in that tail.
- Docs unaffected (the README does not enumerate telemetry rows).
