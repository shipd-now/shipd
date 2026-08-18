## 1. Board drafted state

- [x] 1.1 [req: board-drafted-member] Add failing tests: in
      `plugins/s/skills/build/tests/test_heartbeat.py`, `_OUTCOME_STATE`
      carries an explicit `"drafted": "drafted"` entry and a member
      finishing with outcome `drafted` records roster state `drafted` with
      `stage` cleared; in `plugins/s/skills/build/tests/test_board_activity.py`,
      `_member_column` places a member with roster entry state `drafted` and
      worktree state `archived` in `review` (not `shipped`), and
      `member_signal` returns `{"kind": "drafted", "glyph": "◇", "label":
      "drafted"}` (with `reason` passed through when present) for a drafted
      entry. Run them and observe them fail.
- [x] 1.2 [req: board-drafted-member] In
      `plugins/s/skills/build/scripts/heartbeat.py`, add
      `"drafted": "drafted"` to `_OUTCOME_STATE` (line 38 area) and note the
      first-class mapping in the adjacent comment.
- [x] 1.3 [req: board-drafted-member] In
      `plugins/s/skills/build/scripts/dashboard.py` `_member_column`, add a
      `live == "drafted"` branch returning `"review"`, placed before the
      `live == "shipped" or state == "archived"` branch; update the
      docstring's lane summary.
- [x] 1.4 [req: board-drafted-member] In `dashboard.py` `member_signal`,
      yield the informational drafted signal (kind `drafted`, glyph `◇`,
      label `drafted`, `reason` passthrough) for entry-or-member state
      `drafted`; at the card render sites (`dashboard.py:1817`–`1873` and
      `:2526`–`2529`), style kind `drafted` in an accent/informational tier
      instead of the error color. Update both docstrings; confirm the 1.1
      tests pass.
- [x] 1.5 [req: board-drafted-member] Add one drafted-card render case to
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, mirroring an
      existing parked-card test but asserting the accent-tier styling class
      and the `◇ slug · drafted` text. Run the `tests_textual` suite.

## 2. Doctor pr-mode validation

- [x] 2.1 [req: doctor-pr-mode-check] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: `check_config` on a
      root declaring `"pr-mode": "always"` returns `fail` with a detail
      naming `pr-mode`, the accepted values, and the supplying file; on
      `"pr-mode": "draft"` returns `ok` with the usual content-directory
      detail; with no key, output is unchanged. Run and observe them fail.
- [x] 2.2 [req: doctor-pr-mode-check] In `plugins/s/bin/shipd`
      `check_config`, resolve `sc.resolve_pr_mode(root)` after the
      `specs_dir` resolution inside the same try, so its `ConfigError`
      returns `("fail", "config", str(exc))`; confirm the 2.1 tests pass.

## 3. Documentation

- [x] 3.1 [req: pr-mode-docs] Add a "PR mode — the `pr-mode` key" section
      to `.shipd/README.md` after the autonomous-pipeline section: values
      `auto`/`draft`, the `auto` default, workspace-root layered placement,
      change-shipping-only scope (metadata PRs keep auto-merging), and the
      draft-mode ship behavior (draft PR, no auto-merge, human merges).
- [x] 3.2 [req: pr-mode-docs] Add a `"// pr-mode"` comment entry to
      `plugins/s/skills/build/references/shipd.config.example.json` naming
      the optional key and pointing at the content README's section, without
      declaring a mode.
- [x] 3.3 [req: pr-mode-docs] Add one sentence to `docs/quickstart.md`
      beside the eco-preset opt-in paragraph: declaring
      `{"pr-mode": "draft"}` at a workspace root makes deliveries stop at
      draft PRs for human review.
- [x] 3.4 [req: *] Amend `.shipd/constitution.md`'s "Never commit or push to
      `main` directly" bullet's auto-merging sentence to acknowledge the
      engine's workspace-level `pr-mode: draft` carve-out while stating this
      repo itself declares no `pr-mode` and stays auto-merge-only.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to 0.6.137
      (or the next free patch if a later version already landed on `main`).
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v` (stdlib, no textual/pydantic) and
      `python3 -m unittest discover -s plugins/s/skills/build/tests_textual
      -v` (textual importable locally); confirm both pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 104 | 26.4k |
| Edit | 23 | 10.5k |
| (no tool) | 0 | 4.8k |
| Read | 29 | 3.8k |
| Write | 3 | 2.7k |
| Agent | 2 | 800 |
| SendMessage | 1 | 623 |
| **Total** | 162 | 49.6k |
