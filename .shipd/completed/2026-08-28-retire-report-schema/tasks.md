## 1. The reporter stops accepting and writing the field

- [x] 1.1 [req: persistent-build-log] Add tests to
      `plugins/s/skills/build/tests/test_build_report.py`, following that file's
      existing conventions for driving `--log` against a temporary log
      directory: one asserting the appended entry has no `schema` key at all
      (assert on key absence, not on a null value), and one asserting that
      invoking the reporter with `--schema spec-driven` exits non-zero rather
      than accepting it. Run
      `python3 -m unittest plugins.s.skills.build.tests.test_build_report` and
      observe both fail.
- [x] 1.2 [req: persistent-build-log] In
      `plugins/s/skills/build/scripts/build_report.py`, delete the
      `parser.add_argument("--schema", ...)` line (line 950) so the option is
      removed outright rather than accepted and ignored.
- [x] 1.3 [req: persistent-build-log] In the same file, delete the
      `"schema": args.schema,` entry from the dict the log append builds
      (line 1069), leaving every other key in place and in order.
- [x] 1.4 [req: persistent-build-log] In the same file's module docstring,
      remove `--schema <s>` from the usage line at line 18, leaving the rest of
      that invocation shape unchanged. Confirm 1.1 now passes and the whole
      suite is green.

## 2. The report header drops the label

- [x] 2.1 [req: standard-end-of-build-report] In
      `plugins/s/skills/build/SKILL.md`, change the report template's header
      line (line 686) to
      `Change: {change} — {done}/{total} tasks, Status: {status}`.
- [x] 2.2 [req: standard-end-of-build-report] In the same file, remove
      `--schema <schema>` from the `--log` invocation in Phase 7 step 2
      (line 673), and rewrite that step's opening sentence (line 667) so it no
      longer introduces a schema label — it currently reads "Log the build. The
      `schema` label names the workflow (`spec-driven`); task counts come from
      `claim_task.sh status`." and should keep only the build-logging
      instruction and the task-counts sentence.
- [x] 2.3 [req: standard-end-of-build-report] In
      `plugins/s/harness/references/build.md`, change the report template's
      header line (line 33) to the same
      `Change: {change} — {done}/{total} tasks, Status: {status}`. This file is
      hand-maintained rather than generated from `SKILL.md`, so it needs its own
      edit.

## 3. Verification

- [x] 3.1 [req: *] Confirm the field is gone from the plugin: `grep -rn "schema"
      plugins/s/skills/build/scripts/build_report.py
      plugins/s/skills/build/SKILL.md plugins/s/harness/references/build.md`
      returns no match relating to the build-report schema label.
- [x] 3.2 [req: *] Run the full build test suite —
      `python3 -m unittest discover -s plugins/s/skills/build/tests -t .` — and
      confirm it reports OK with no failures. The `test_build_report` baseline
      on the clean worktree was 55 tests, so that module must report at least
      55 plus the two added in task 1.1.
- [x] 3.3 [req: *] Confirm nothing else in the plugin still passes or reads the
      option: `grep -rn -- "--schema" plugins/s` returns no match.

## 4. Ship the plugin snapshot

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.158`, so the
      cached plugin snapshot picks up these `plugins/s/` edits (AGENTS.md: every
      change touching `plugins/s/` bumps the version in the same PR).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 112 | 33.2k |
| (no tool) | 0 | 4.0k |
| Read | 16 | 2.8k |
| Edit | 8 | 2.2k |
| Agent | 2 | 1.5k |
| **Total** | 138 | 43.7k |
