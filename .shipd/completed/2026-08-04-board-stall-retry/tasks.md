## 1. Autopilot stale-worktree reclaim

- [x] 1.1 [req: stale-worktree-reclaim] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add tests driving a
      member through a scripted `command_fn` covering: create fails `already
      exists` → guarded remove (argv `["env", "SHIPD_WORKTREE_IDLE_MINUTES=0",
      <worktree.sh>, "remove", <slug>]`) → `git show-ref` → `git branch -d` →
      retried create succeeds → member proceeds; guarded remove exits 2 →
      member parks `needs_human` at stage `worktree` with the refusal output as
      reason; `git branch -d` fails → parks with its output as reason; create
      fails without `already exists` → parks as today with no reclaim argv
      issued. Run them and observe them fail.
- [x] 1.2 [req: stale-worktree-reclaim] In
      `plugins/s/skills/build/scripts/autopilot.py`, in `drive_member`'s
      worktree step, implement the reclaim: when the create's stderr contains
      `already exists`, (1) if `os.path.isdir(<root>/.worktrees/<slug>)` run
      `["env", "SHIPD_WORKTREE_IDLE_MINUTES=0", WORKTREE_SH, "remove", slug]` via
      `command_fn`, parking `needs_human`/`worktree` with the output as reason
      on non-zero; (2) if `["git", "show-ref", "--verify", "--quiet",
      "refs/heads/change/<slug>"]` exits 0, run `["git", "branch", "-d",
      "change/<slug>"]`, parking with its output on non-zero; (3) retry
      `[WORKTREE_SH, slug]` once, parking as today on a second failure. Other
      create failures keep today's parking path untouched. Confirm the 1.1
      tests pass.

## 2. Board stall predicate and header marker

- [x] 2.1 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add pure
      tests for `epic_stalled` / `stalled_entries`: finished heartbeat with a
      `needs-human` entry → stalled, entries returned with `slug`/`stage`/
      `reason`; finished heartbeat with only `rejected`/`shipped` entries →
      not stalled; running heartbeat with a `needs-human` entry → not stalled;
      missing heartbeat → not stalled. Also assert
      `epic_group_title(..., stalled=True)` prefixes `[$text-error]✗[/] `
      before the slug and `stalled=False` leaves today's title byte-identical.
      Run and observe failure.
- [x] 2.2 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the pure helpers
      `epic_stalled(epic)` and `stalled_entries(epic)` reading only
      `epic.get("heartbeat")` (run `state == "finished"` and roster entries
      with `state == "needs-human"`), and give `epic_group_title` a
      `stalled=False` keyword that prefixes `[$text-error]✗[/] ` to the
      returned title. Confirm the 2.1 tests pass.
- [x] 2.3 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      signature test: two `_lane_signature` calls over the same cards whose
      entry differs only in `state` (`needs-human` vs `driving`, same stage)
      produce different signatures. Observe it fail; then in
      `plugins/s/skills/build/scripts/dashboard.py` add
      `entry.get("state")` to the per-card tuple in `_lane_signature` and
      confirm it passes.
- [x] 2.4 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`'s `_render_lanes` (the
      `epic_group_title` call site), pass
      `stalled=epic_stalled(<that group's epic dict>)` so stalled epics render
      the marker; extend an existing grouped-render test in
      `tests_textual/test_dashboard.py` with a stalled-heartbeat fixture
      asserting the mounted group header title carries the `✗` marker.

## 3. Epic-detail warning and Retry

- [x] 3.1 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add
      `EpicDetailScreen` tests over a stalled-epic fixture: the modal renders
      a warning block naming each `needs-human` member with its stage and
      reason and a `Retry` button (`id="epic-retry"`); pressing Retry calls
      `dispatch_epic_run` with the epic slug (stub it recording calls, the
      `EpicRunConfirmScreen` test pattern) and dismisses the modal; a
      non-stalled epic's modal mounts neither warning nor Retry. Run and
      observe failure.
- [x] 3.2 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, extend
      `EpicDetailScreen.compose` to render, when `epic_stalled(epic)`, a
      warning `Static` (`stalled: <n> member(s) parked needs-human`) plus one
      `markup=False` line per `stalled_entries` entry (`<slug>  <stage>
      <reason>`) and a `Retry` button (`id="epic-retry"`) between the header
      rule and the member list; handle it in `on_button_pressed` by calling
      `self.app.dispatch_epic_run(self.epic_slug)` then `self.dismiss()`.
      Confirm the 3.1 tests pass.

## 4. Ship

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.45`.
- [x] 4.2 [req: *] Run both suites — `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests_textual` (after `pip install -r
      requirements.txt`) — and confirm green.
