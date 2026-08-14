# Tasks — synthetic-filter

## 1. Filter and tests

- [x] 1.1 [req: synthetic-records-excluded] Add failing tests in
      `plugins/s/skills/build/tests/test_build_report.py`: aggregating a
      transcript fixture containing a real-model record, a `<synthetic>`
      zero-usage record between two real records, and a zero-usage
      real-model record yields a `by_model` without `<synthetic>`, keeps the
      zero-usage real model, and produces per-model times that sum to the
      total with nothing attributed to `<synthetic>`. Run and observe the
      new tests fail.
- [x] 1.2 [req: synthetic-records-excluded] In
      `plugins/s/skills/build/scripts/build_report.py`, add
      `SYNTHETIC_MODEL = "<synthetic>"` and skip matching records in
      `aggregate()`'s record loop before usage accumulation and
      `timeline.append`, per the plan's Implementation. Confirm the 1.1
      tests pass.
- [x] 1.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.5` → `0.2.6`.

## 2. Verification

- [x] 2.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py synthetic-filter`;
      everything green.
