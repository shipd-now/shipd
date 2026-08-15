## 1. Shared board-lane projection

- [x] 1.1 [req: epic-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing unit
      tests for a pure `spec_status.board_lane(state)`: `archived`→`shipped`,
      `ready`→`ready`, `unplanned`→`unplanned`, and each of `draft`,
      `active`, `complete`, `verified`, `rejected`, `?`→`building`. Run them
      and observe the failure — the function does not exist yet.
- [x] 1.2 [req: epic-status-verbs] Implement `board_lane(state)` in
      `plugins/s/skills/build/scripts/spec_status.py` exactly per 1.1's
      mapping; confirm 1.1's tests pass.
- [x] 1.3 [req: epic-status-verbs] In
      `plugins/s/skills/build/scripts/dashboard.py`, make `flow_lane`
      (dashboard.py:261) delegate to `ss.board_lane`, keeping its name,
      signature, and docstring (update the docstring's mirror note to name
      the shared function). Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (no
      `textual` installed) and confirm it passes.

## 2. Board-shaped epic report

- [x] 2.1 [req: epic-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, update the
      `epic-show` assertions (the flat `<mslug>: <state>` expectations
      around lines 516 and 686-740) to the lane-grouped report and add
      failing tests covering: the unchanged `<slug>: <status>` first line
      and metadata lines; the `shipped <n>/<m>` line; lane order
      `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` with `<LANE> (<count>)`
      headers including `(0)` for empty lanes; member lines carrying slug,
      state, `risk <value>` from the stub-table's last rating cell (`?`
      when absent); and the `[worktree]` marker for a worktree-derived
      state. Run them and observe the failure.
- [x] 2.2 [req: epic-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `_epic_report_lines(root, slug)` building the report of 2.1 (reusing
      `_member_state_with_root`, `parse_epic_changes` ratings, and
      `board_lane`) and rework `cmd_epic_show` (spec_status.py:737) to
      print it; confirm 2.1's tests pass.
- [x] 2.3 [req: epic-status-verbs] Update the usage banner line for
      `epic-show` (spec_status.py:32) and its argparse `help` string
      (spec_status.py:1671) to say it prints the board-shaped epic report.

## 3. status/show epic fallback

- [x] 3.1 [req: status-cli] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing
      tests: `status <epic-slug>` (no change of that name) prints the
      epic's status and exits 0; `show <epic-slug>` prints byte-identical
      output to `epic-show <epic-slug>`; a name matching neither change
      nor epic still prints `?` from `status`. Run them and observe the
      failure.
- [x] 3.2 [req: status-cli] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend `cmd_status`
      (spec_status.py:402) and `cmd_show` (spec_status.py:388): when
      `_is_change` is false for the resolved name and
      `os.path.isfile(_epic_path(root, name))`, print the epic status
      (`status`) or `_epic_report_lines` (`show`); otherwise behavior is
      unchanged. Confirm 3.1's tests pass.

## 4. Skill wrapper and plugin snapshot

- [x] 4.1 [req: interactive-status-skill] In
      `plugins/s/skills/status/SKILL.md`, document that
      `/s:status [change]`'s argument may name an epic — the CLI then
      reports the board-shaped epic report, which the skill relays — and
      that epic transitions go through `epic-set-status`, never
      `set-status`.
- [x] 4.2 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` (patch bump).
- [x] 4.3 [req: *] Run the full suite
      `python3 -m unittest discover -s plugins/s/skills/build/tests` without
      `textual` installed and confirm everything passes.
