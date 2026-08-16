## 1. Cumulative-snapshot counting in the activity tail

- [x] 1.1 [req: session-activity-sampling] In
      `plugins/s/skills/build/tests/test_build_report.py`'s `ActivityTail`
      test class, add tests: (a) two records sharing one message id with
      `output_tokens` 1 then 104 in one poll yield events summing 104, the
      delta event timestamped at the later record; (b) records repeating an
      unchanged snapshot for one id — within a poll and again across polls —
      yield an event only for the first record; (c) a higher snapshot for an
      already-seen id arriving in a later poll yields the delta so the
      response still sums to its final value. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p
      "test_build_report.py" -q` and observe the new tests fail.
- [x] 1.2 [req: session-activity-sampling] In
      `plugins/s/skills/build/scripts/build_report.py`, replace
      `ActivityTail._seen_ids` (set) with a dict mapping message id → highest
      `output_tokens` snapshot counted; in `_event`, yield the first sighting
      of an id at its snapshot as today, yield only the positive delta (at
      the record's own timestamp, updating `_prev_end`) for a later record of
      a seen id, and yield nothing on an equal-or-lower snapshot; a record
      with no message id still yields in full. Update the class docstring's
      dedupe sentence to the delta rule. Confirm 1.1's tests pass.

## 2. Cumulative-snapshot counting in the build report

- [x] 2.1 [req: usage-dedup] In the same test module's usage-dedup test
      class, add tests: (a) three records sharing one message id with
      `output_tokens` 1, 1, 331 sum to 331 in the per-model summary; (b) two
      records sharing an id whose later record raises `input_tokens` and
      `cache_read_input_tokens` leave the summary at the later record's
      values; (c) the timeline still records every timestamped record. Run
      the module's tests and observe the new ones fail.
- [x] 2.2 [req: usage-dedup] In
      `plugins/s/skills/build/scripts/build_report.py`'s `aggregate`,
      replace `seen_ids` (set) with a dict mapping message id → per-field
      highest-counted values for `input_tokens`, `output_tokens`,
      `cache_creation_input_tokens`, and `cache_read_input_tokens`, adding
      each field's positive delta to the model bucket; a record with no
      message id still counts in full; timeline appending is unchanged.
      Update the in-function comment to the delta rule. Confirm 2.1's tests
      pass.

## 3. Verification and snapshot hygiene

- [x] 3.1 [req: *] Run the full stdlib-only suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q`, and
      confirm every test passes without `textual` installed.
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.106 to 0.6.107 (the
      cache-snapshot rule for any `plugins/s/` change).
