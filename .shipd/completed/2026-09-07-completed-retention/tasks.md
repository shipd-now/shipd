## 1. Config key — completed_retention_days

- [x] 1.1 [req: completed-retention-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add a test class for
      the retention key covering: undeclared → accessor yields 30 and
      `resolve_config` reports the key with `default` provenance; a declared
      positive int (e.g. 7) wins over an outer layer's value; declared `0` →
      accessor yields `None`; declared `null` → `None`; declared `"forever"`,
      `true`, and `-5` → accessor yields 30 with no error. Run it and observe
      it fail — the accessor does not exist yet.
- [x] 1.2 [req: completed-retention-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `COMPLETED_RETENTION_KEY = "completed_retention_days"` and
      `DEFAULT_COMPLETED_RETENTION_DAYS = 30` beside `DEFAULT_DIR`; seed the
      key into `resolve_config`'s initial defaults dict (next to `"dir"`); add
      `def completed_retention_days(config)` returning the window in days or
      `None` when disabled: `None` value → `None`; `int` (not `bool`) and
      `> 0` → the value; `0` → `None`; anything else → the default. Confirm
      the 1.1 tests pass.
- [x] 1.3 [req: completed-retention-key] In
      `plugins/s/skills/build/tests/test_spec_status.py`'s config-show test
      class (near `test_defaults_only_succeeds`), add a test asserting a
      defaults-only `config-show` run's stdout contains
      `completed_retention_days = 30` with `default` provenance on that line.
      Run the class and confirm it passes (config-show already prints every
      resolved key; no spec_status.py change is expected).

## 2. Board retention filter

- [x] 2.1 [req: board-completed-retention] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      retention test class with a fixture root holding: a `complete` epic
      whose member archive dir under `completed/` is stamped 40 days before an
      injected `today`; a `complete` epic stamped 5 days before; an `active`
      epic with one 40-day-old archived member and one `planned/` member; a
      standalone archived change (worktree-hosted, no `Epic:` line) stamped 40
      days back; and a `complete` epic whose archive dir name carries no date
      prefix. Assert via `dashboard.build_board(root, retention_days=30,
      today=<fixed date>)`: the old complete epic is absent from `epics` and
      `groups`; the recent one present; the active epic present with both
      members; the old standalone row absent; the undatable epic present;
      `board["hidden_completed"] == 2` and `board["retention_days"] == 30`;
      with `retention_days=None` nothing is hidden and `hidden_completed` is
      0; with `epic=<old slug>` the epic aggregates. Run and observe failure —
      the parameters do not exist yet.
- [x] 2.2 [req: board-completed-retention] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the filter:
      add `_archive_date(location, slug)` (glob
      `sc.specs_dir(location)/completed/*-<slug>`, newest dirname, parse a
      leading `YYYY-MM-DD` via `datetime.date`; return `None` on no match, a
      parse failure, or `sc.ConfigError`) and `_epic_completion_date(epic)`
      (max `_archive_date` over stub members, else `None`). Change
      `build_board(root, epic=None)` to
      `build_board(root, epic=None, retention_days=_RESOLVE, today=None)`
      with a module-level `_RESOLVE` sentinel: the sentinel resolves the
      window via `sc.completed_retention_days(sc.resolve_config(root)[0])`;
      when `epic` is not None or the window is `None`, skip filtering. Before
      `_group_epics` runs, drop each epic with status `complete` whose
      completion date precedes `today - timedelta(days=N)` (default `today` =
      `datetime.date.today()`), and each standalone row with state `archived`
      whose `_archive_date` precedes it; count the drops. Set
      `board["hidden_completed"]` (0 when nothing hidden) and
      `board["retention_days"]` (the applied window, `None` when disabled or
      epic-scoped). Confirm the 2.1 tests pass.
- [x] 2.3 [req: board-completed-retention] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      renderer test: `render_board_lines` on a board dict with
      `hidden_completed: 3` and `retention_days: 30` ends with a line
      containing `3 older completed hidden` and `completed_retention_days=30`,
      and emits no such line when `hidden_completed` is 0 or absent. Run and
      observe failure, then implement the trailing note line in
      `render_board_lines` in `plugins/s/skills/build/scripts/dashboard.py`
      and confirm the test passes.

## 3. Verb flags and TUI surface

- [x] 3.1 [req: board-completed-retention] In
      `plugins/s/skills/build/scripts/dashboard.py`, add
      `--all` (`action="store_true"`, help: show completed work beyond the
      retention window) to both the `board` and `tui` subparsers in `main`;
      in `_cmd_board` pass `retention_days=None` when `args.all`; give
      `BoardApp.__init__` a `show_all=False` keyword, defaulting its
      `board_fn` lambda to pass `retention_days=None` when `show_all`, and
      wire `_cmd_tui` to pass `show_all=args.all`.
- [x] 3.2 [req: board-completed-retention] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a TUI
      test (mirroring the existing `run_test`-style lane tests) asserting
      that with a board whose `hidden_completed` is 2 the shipped lane's
      `.lane-header` Static text contains `2` and `older hidden`, and that it
      reads plain `SHIPPED` when nothing is hidden. Run and observe failure,
      then implement: in `BoardApp._render_lanes` (dashboard.py), update the
      shipped `Lane`'s `.lane-header` Static to
      `SHIPPED · <n> older hidden` when `self.board.get("hidden_completed")`
      is positive, restoring `SHIPPED` otherwise. Confirm the test passes.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.184` to `0.6.185` (or
      the next patch above the value found on the branch).
- [x] 4.2 [req: *] Run both suites and confirm green:
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (no
      `textual` required) and, with `pip install -r requirements.txt`,
      `python3 -m unittest discover -s plugins/s/skills/build/tests_textual`.

## 5. Fix — unreadable root config fails open

- [x] 5.1 [req: board-completed-retention] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      regression test: a fixture root whose `.shipd-config.json` is malformed
      JSON (e.g. `{"dir": ".shipd",}`) — `build_board(root)` (default
      retention resolution) returns a board with `hidden_completed == 0` and
      `retention_days is None` and raises nothing; `main(["board", "--root",
      <root>])` exits 0 with no traceback. Run and observe it fail (the
      `_RESOLVE` sentinel path lets `sc.ConfigError` escape), then fix
      `dashboard.py`: wrap the sentinel resolution's
      `sc.resolve_config(root)` in `try/except sc.ConfigError`, treating an
      unreadable config as a disabled window (`None`). Confirm the test
      passes and both suites stay green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 88 | 25.9k |
| Write | 4 | 9.7k |
| Edit | 25 | 4.1k |
| (no tool) | 0 | 1.8k |
| Read | 22 | 942 |
| Agent | 2 | 871 |
| **Total** | 141 | 43.3k |
