## 1. Column grammar and parser

- [ ] 1.1 [req: epic-artifact-layout] In
      `plugins/s/skills/build/tests/test_spec_common.py` add tests:
      `parse_epic_changes` on a seven-column table returns ratings of
      exactly four cells for every row; `parse_epic_after(text)` returns
      `{"a": [], "b": ["a"], "c": ["a", "b"]}` for cells ``, `a`, `a, b`
      and all-empty lists for a six-column table. Run them and observe the
      failures.
- [ ] 1.2 [req: epic-artifact-layout] In
      `plugins/s/skills/build/scripts/spec_common.py` add
      `EPIC_AFTER_COLUMN = "After"` under `EPIC_CHANGES_COLUMNS`, slice
      `ratings` in `parse_epic_changes` to
      `cells[2:2 + len(EPIC_CHANGES_COLUMNS) - 2]`, and add
      `parse_epic_after(text)` returning `{slug: [slugs]}` from the seventh
      cell split on commas with whitespace stripped (empty lists when the
      header lacks the column). Run the 1.1 tests until they pass.

## 2. Lint

- [ ] 2.1 [req: epic-structural-validation] In
      `plugins/s/skills/build/tests/test_spec_lint.py` add tests on a
      fixture epic: seven-column header with `b` after `a` lints clean; a
      cell `b, zz` on row `b` reports a self-reference and an unknown slug;
      `a` after `b` and `b` after `a` lints clean; a seven-column header
      whose seventh column is `Later` is reported as a bad header. Run them
      and observe the failures.
- [ ] 2.2 [req: epic-structural-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py` `_check_epic_changes`
      accept a header equal to the six columns or the six plus
      `EPIC_AFTER_COLUMN`; when the latter, read `parse_epic_after` and error
      per slug that fails `KEBAB_RE`, names no row, or names its own row.
      Run the 2.1 tests until they pass.

## 3. Plan waves

- [ ] 3.1 [req: member-wave-scheduling] In
      `plugins/s/skills/build/tests/test_autopilot.py` extend `_make_epic`
      with an optional `after` mapping that emits the seventh column, and
      add tests for the four new scenarios in the `epic-autopilot` delta
      (layered waves with `after` lists, satisfied dependency, cycle
      serialised after `z`, and the no-column case still chunking by risk).
      Run them and observe the failures.
- [ ] 3.2 [req: member-wave-scheduling] In
      `plugins/s/skills/build/scripts/autopilot.py` give `Member` an
      `after: list` field filled by `parse_members` from
      `parse_epic_after`; in `compute_waves`, when any unplanned member has
      a non-empty `after`, replace the chunk loop with Kahn layering over
      unplanned-only edges (layer sort: `RISK_RANK` then `order`; chunk to
      `parallel`), then one wave per leftover cycle member in `order`;
      add `"after"` to `_entry`; make `_print_waves` append `after a, b`
      to a plan-wave member when non-empty. Run the 3.1 tests until they
      pass, then run the whole `tests/` suite.

## 4. Grill skill

- [ ] 4.1 [req: epic-grill-preflight-order, epic-grill-planner-contract] In
      `plugins/s/skills/build/tests/test_epic_grill_contract.py` add tests
      that `skills/epic-grill/SKILL.md` and `harness/bodies/epic-grill.md`
      both name `--waves --parallel`, the phrase `wave by wave`, and state
      that sibling members of one wave are not named in each other's
      instruction. Run them and observe the failures.
- [ ] 4.2 [req: epic-grill-preflight-order] In
      `plugins/s/skills/epic-grill/SKILL.md` Preflight, add the optional
      `--parallel N` argument (default 3) and a step that, when the table
      carries a non-empty `After` cell, runs
      `autopilot.py <epic> --waves --parallel N --json` and prints each plan
      wave with its members' `after` lists; keep the judged order for a
      table without the column.
- [ ] 4.3 [req: epic-grill-planner-contract] In
      `plugins/s/skills/epic-grill/SKILL.md` Planning, rewrite the loop to
      run wave by wave: spawn one sub-agent per wave member in a single
      message, brief each with every earlier wave's roots only, wait for the
      wave, grade each member, re-lint every earlier member, then start the
      next wave; a wave of one is the serial path.
- [ ] 4.4 [req: epic-grill-preflight-order, epic-grill-planner-contract]
      Mirror 4.2 and 4.3 in `plugins/s/harness/bodies/epic-grill.md` steps
      1–3, keeping its single-session phrasing. Run the 4.1 tests and
      `test_harness_bodies.py` until they pass.

## 5. Epic authoring

- [ ] 5.1 [req: epic-interview-skill] In
      `plugins/s/skills/epic/SKILL.md` add `After` to the contract's stub
      table example and to the Stub table rule (six columns or six plus
      `After`; cells name sibling slugs from the Design's seams, empty when
      none), and instruct authoring to fill it; mirror the table in
      `plugins/s/harness/bodies/epic.md`.
- [ ] 5.2 [req: epic-interview-skill] Add a test in
      `plugins/s/skills/build/tests/test_epic_grill_contract.py` asserting
      both epic surfaces name the `After` column; run it.

## 6. Release

- [ ] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to one patch
      above `main`'s current value, run
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, and
      `spec_lint.py --epic pr-room` to confirm the six-column epic still
      lints clean.
