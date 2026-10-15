## 1. Shared cited-token helpers

- [x] 1.1 [req: drift-verb] In
      `plugins/s/skills/build/tests/test_spec_common.py`, after
      `PlanMetadataParserTest` (line 275), add `CitedTokensTest`:
      `cited_paths` on a text with `` `src/a.py` ``, `` `./x/y` ``,
      `` `https://e.com/p` ``, `` `name` ``, `` `src/a.py:12-14` ``, and a
      repeated `` `src/a.py` `` returns `["src/a.py", "./x/y"]`, and with
      `strip_line_suffix=True` still one `src/a.py`; `cited_symbols` on
      `` `old_helper` ``, `` `sc.content_hash` ``, `` `--check` ``,
      `` `read_plan_stamp(text)` ``, `` `src/a.py` ``, and `` `two words` ``
      returns `["old_helper", "sc.content_hash", "--check",
      "read_plan_stamp"]`; `VERSION_BUMP_EXEMPT_PATHS ==
      ("plugins/s/.claude-plugin/plugin.json",)`; `PATH_TOKEN_RE` and
      `BACKTICK_RE` exist on `spec_common`. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_spec_common` and observe the failures.
- [x] 1.2 [req: drift-verb] In `plugins/s/skills/build/scripts/spec_common.py`
      after `parse_plan_metadata` (line 3013): add `BACKTICK_RE` and
      `PATH_TOKEN_RE` (the exact patterns from `spec_gate.py:74-76`),
      `LINE_SUFFIX_RE`, `CALL_SUFFIX_RE`, `SYMBOL_TOKEN_RE`,
      `VERSION_BUMP_EXEMPT_PATHS`, `cited_paths(text, strip_line_suffix=False)`
      and `cited_symbols(text)` as `plan.md` "Cited tokens" specifies, each
      with a docstring citing the drift-verb requirement. Re-run 1.1 until it
      passes.
- [x] 1.3 [req: drift-verb] In `plugins/s/skills/build/scripts/spec_gate.py`:
      replace the local `BACKTICK_RE`/`PATH_TOKEN_RE` definitions (lines
      70-76) with `BACKTICK_RE = sc.BACKTICK_RE` and `PATH_TOKEN_RE =
      sc.PATH_TOKEN_RE`, and make `_check_task_paths` iterate
      `sc.cited_paths(text)` instead of its own backtick loop, keeping the
      existence, `artefacts/`, parent, and grandparent logic unchanged; update
      the module docstring's check 3 to name the shared helper. Run
      `python3 -m unittest plugins.s.skills.build.tests.test_spec_gate` — all
      existing tests pass unchanged.
- [x] 1.4 [req: drift-verb] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch above `main`
      (`0.6.292` at planning time).

## 2. Check-base findings seam

- [x] 2.1 [req: drift-verb] In `plugins/s/skills/build/scripts/spec_status.py`
      split `cmd_check_base` (line 1289): move the loop that builds the
      `(capability, id, kind, detail)` list into
      `check_base_findings(root, change)` returning that list, and leave
      `cmd_check_base` to call it and print exactly as today. Run `python3 -m
      unittest plugins.s.skills.build.tests.test_spec_status.CheckBaseTest`
      — passes unchanged.

## 3. Single-change drift

- [x] 3.1 [req: drift-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py` after `CheckBaseTest`
      (line 6738), add `DriftTest(SpecStatusTestBase)` with helpers:
      `_init_git` (`git init -q -b main`, user config, add, commit — mirror
      line 4568), `_git(*args)` returning stdout, `_commit_all(msg)`, and
      `make_stamped_change(change, planned_at, citations)` writing a plan with
      `Status: ready` and `Planned-at: <sha>` whose `## Implementation` holds
      the given backticked citations. Fixture: `src/engine.py` with
      `def old_helper():` and `def kept():`, committed on `main`. Tests:
      a plan citing `src/engine.py`, `old_helper`, `kept`, `new_verb`, and
      `src/engine.py:3-4`, stamped at `HEAD`, then a commit removing
      `old_helper` from `src/engine.py` → `drift <change>` exits 4, prints
      `planned-at: <sha> (stamp)`, `base: main <sha>`, `file-drift
      src/engine.py 1 (<short sha>)`, `symbol-gone old_helper`, and neither
      `kept` nor `new_verb`, summary `drift: 1 finding(s).` counts every
      finding; no commit since the stamp → exit 0 and `drift: clean (no
      findings).`; a commit touching only
      `plugins/s/.claude-plugin/plugin.json` (cited) → exit 0; a master
      requirement edited after the delta's `base:` was taken → a
      `stale-base <cap>/<id> (expected ..., actual ...)` line; a committed
      plan without `Planned-at` → `planned-at: <plan commit sha>
      (plan-commit)`; an uncommitted unstamped plan → exit 1 and stderr
      naming `Planned-at` and `spec_gate.py`; a `Planned-at` sha absent from
      the repo → exit 1; `--base nosuch` → exit 1; `--json` parses as one
      object with `change`, `root`, `planned_at`, `stamp_source`, `base.ref`,
      `base.sha`, and a `file-drift` finding carrying `path` and `commits`;
      the content directory is byte-identical before and after
      (`snapshot_content` as `CheckBaseTest` does). Run and observe the
      failures.
- [x] 3.2 [req: drift-verb] In `spec_status.py` under a new "Drift (spec-status
      drift-verb)" section after `cmd_base_hash`: add `_drift_stamp`,
      `_drift_cited(change_dir)` (paths and symbols from `plan.md`,
      `tasks.md`, `specs/*/spec.md` via `sc.cited_paths(text, True)` and
      `sc.cited_symbols`, dropping `artefacts/` and
      `sc.VERSION_BUMP_EXEMPT_PATHS`), `_drift_file_findings`,
      `_drift_symbol_findings` (the base-then-stamp two-call `git grep`),
      `_drift_measure(hosting_root, change, base_ref, base_sha)` returning
      the single-change dict, `_drift_render(result)` returning the text
      lines, and `cmd_drift(root, change, epic, base, as_json)` handling the
      single-change form exactly as `plan.md` "Text shape", "JSON shape",
      and "Single-change unmeasurable" specify. Add the `drift` subparser
      (`change` `nargs="?"`, `--epic`, `--base` default
      `DEFAULT_AMEND_BASE`, `_add_json_flag`) next to `check-base` (line
      4707) and the dispatch next to it (line 4982); add `drift` to the
      module docstring verb list and its exit-code paragraph. Re-run 3.1
      until it passes.

## 4. Epic mode

- [x] 4.1 [req: drift-epic-mode] In `DriftTest`, add epic tests: an
      `epics/e/epic.md` whose `## Changes` table lists `a`, `b`, `c` (plus
      an `After` column) with `a` stamped and drifted under the root, `b`
      stamped and clean under `.worktrees/wt/.shipd/planned/b/`, and `c`
      unplanned → `drift --epic e` exits 4, prints two blocks whose `root:`
      lines name the root and `.worktrees/wt`, separated by a blank line,
      then `skipped: c (unplanned)` and `drift: N finding(s).`; an epic whose
      only planned member is unstamped and uncommitted → `skipped: <m>
      (no-stamp)`, `drift: clean (no findings).`, exit 0; `--epic e --json`
      parses as one object with `epic`, `base`, `members`, `skipped`;
      `drift a --epic e` exits 2 with usage on stderr; `drift --epic nosuch`
      exits 1. Run and observe the failures.
- [x] 4.2 [req: drift-epic-mode] In `spec_status.py` `cmd_drift`: implement
      the `--epic` branch per `plan.md` "`--epic`": `parser.error` on both
      forms, `_epic_hosting_root` (error when `None`), `_epic_rows` in table
      order, `_member_state_with_root` per member, `skipped` for
      `unplanned`/`archived`/`no-stamp`/`unknown-stamp`, blocks from
      `_drift_render`, skipped lines, summary, exit 4 on any finding; JSON
      object with `epic`, `base`, `members`, `skipped`. Re-run 4.1 until it
      passes.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests`; then from the worktree run `python3
      plugins/s/skills/build/scripts/spec_status.py drift drift-verb` and
      `... drift --epic autopilot-preflight --json`, confirming the first
      reports this change from its plan commit and the second lists the
      unplanned siblings under `skipped`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 91 | 1.6k |
| ToolSearch | 4 | 1.0k |
| (no tool) | 0 | 1.0k |
| Agent | 2 | 124 |
| TaskStop | 1 | 63 |
| SubagentHandback | 3 | 53 |
| SendMessage | 2 | 26 |
| **Total** | 103 | 3.9k |
