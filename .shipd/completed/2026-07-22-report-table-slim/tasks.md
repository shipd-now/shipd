## 1. Renderer

- [x] 1.1 Rework `render_table` in
      `plugins/s/skills/build/scripts/build_report.py` to the design.md D1/D2
      column set `Model | Tokens ↑ | Tokens ↓ | Token % | Time`: drop the
      Cache ↑/Cache ↓ and Time % columns, add Token % (whole-percent share of
      total non-cached output tokens, Total row 100%, all rows 0% when total
      output is zero), keep the Total row, the trailing `Total time:` line,
      and the existing drop-the-Time-column degradation when timing is
      unavailable. Touch nothing in the summary line, `--json`, or `--log`
      paths.

## 2. Tests

- [x] 2.1 Add `plugins/s/skills/build/tests/test_build_report.py` (stdlib
      unittest, direct import of `build_report` via the sibling-import
      pattern) asserting per design.md D3: exact header columns and order,
      per-row Token % arithmetic on a two-model fixture, Total row 100%, no
      `Cache` or `Time %` strings anywhere in the output, the `Total time:`
      line present, and the zero-output edge case rendering 0%.

## 3. End-to-end

- [x] 3.1 Run the full test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and a
      live check from the repo root:
      `python3 plugins/s/skills/build/scripts/build_report.py --since <one hour ago> --table`
      must print the new five-column table with a plausible Token % column
      and no cache columns. Report the observed table.
