## 1. Per-tool breakdown verb in build_report

- [x] 1.1 [req: tool-usage-breakdown] In
      `plugins/s/skills/build/tests/test_build_report.py`, add a test class
      for the per-tool breakdown covering: a 100-token response with `Bash` +
      `Read` tool_use blocks splits 50/50 with one call each; a text-only
      response lands in `(no tool)` with zero calls; a subagent transcript's
      `Bash` response merges into the same row as the main transcript's; a
      message id spanning snapshots 1, 1, 331 attributes 331 once; the
      `**Total**` row equals the deduplicated sum; rows sort by output tokens
      descending; `--since` newer than all records prints nothing with exit
      0. Run `python3 -m unittest discover -s plugins/s/skills/build/tests
      -p "test_build_report.py" -q` and observe the new tests fail.
- [x] 1.2 [req: tool-usage-breakdown] In
      `plugins/s/skills/build/scripts/build_report.py`, add an aggregation
      helper that walks the resolved session's main and subagent transcript
      paths, groups assistant records by message id (skipping synthetic
      models, honoring `since_dt`), takes each response's final usage
      snapshot (per-field maximum) and the union of its records' `tool_use`
      block names, and returns per-tool `(calls, output_tokens)` with even
      integer split (remainder to the first-listed tool) plus a `(no tool)`
      bucket; add a renderer for the `## Token usage breakdown` markdown
      section and a `--tool-table` flag in `main()` wired like `--table`.
      Confirm 1.1's tests pass.

## 2. Build flow writes the change table

- [x] 2.1 [req: tool-usage-breakdown] In
      `plugins/s/skills/build/SKILL.md`, add a step immediately before the
      Phase-6 `spec_merge` invocation: generate the section with
      `build_report.py --since "$BUILD_START" --tool-table` and, when
      non-empty, write it as the trailing section of
      `planned/<change>/tasks.md` (replacing an existing
      `## Token usage breakdown` section) so it archives with the change;
      note that a failure here never blocks the merge, matching Phase 7's
      degrade-gracefully rule.

## 3. Epic aggregation in epic-sync

- [x] 3.1 [req: epic-token-breakdown] In
      `plugins/s/skills/build/tests/test_spec_status.py`'s epic-sync test
      class, add tests: two archived members' tables (each `Bash` 100
      tokens, 1 call) sum to a `Bash` row of 200/2 with Total 200; a second
      unchanged run leaves `epic.md` byte-identical; a member without a
      table contributes nothing without error; with no member tables an
      existing epic section is removed; a `draft` epic's file is untouched.
      Run the module and observe the new tests fail.
- [x] 3.2 [req: epic-token-breakdown] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend
      `cmd_epic_sync` with a stdlib-only aggregation step: resolve each
      member's archived change the way `_member_state` already resolves it,
      parse the trailing `## Token usage breakdown` table from the archived
      `tasks.md` (skipping unparseable tables), sum per-tool calls and
      output tokens, and idempotently replace (or remove, when empty) the
      epic file's trailing section while preserving the draft guard and all
      other content. Confirm 3.1's tests pass.

## 4. Verification and snapshot hygiene

- [x] 4.1 [req: *] Run the full stdlib-only suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q`, and
      confirm every test passes without `textual` installed.
- [x] 4.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` one patch above the value on
      current `main` at build time (after `subagent-token-tracking` merges,
      e.g. 0.6.105 → 0.6.106) — the cache-snapshot rule for any `plugins/s/`
      change.
