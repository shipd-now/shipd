# epic-status-report
Status: verified

## Idea

Make the status CLI report an epic the way the delivery board shows it —
members grouped into the board's lifecycle lanes — and let `status`/`show`
fall back to the epic when their argument names one.

### Motivation

`spec_status.py status shipd-port` prints `?` because `status`/`show` treat
every argument as a change, while the board presents the same slug as an epic
whose members are bucketed into lanes; the user expects status output to be a
reflection of what the board shows.

### Details

- `status`/`show` fall back to the epic when the argument names no change but
  `epics/<name>/epic.md` exists: `status` prints the epic's status value,
  `show` prints the board-shaped epic report.
- `epic-show` becomes that board-shaped report: unchanged `<slug>: <status>`
  first line and metadata lines, then `shipped <n>/<m>`, then the four board
  lanes in board order with counts and one member line each (state, risk,
  `[worktree]` marker).
- A single pure state→lane projection lives in `spec_status.py`;
  `dashboard.py`'s `flow_lane` delegates to it so board and report cannot
  drift.
- The `/s:status` skill documents epic reporting; plugin version bump.

Affected capabilities: `spec-status` (modified). Impact:
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/status/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.
No new dependencies — stdlib only.

### Non-goals

- No heartbeat reads: no `review` lane, no stale/dead-run markers — live-run
  lanes remain the dashboard's concern (state-only projection).
- No change to transitions: epic transitions stay on `epic-set-status`;
  `set-status` remains change-only.
- No fallback for archived changes: `status <completed-change>` still prints
  `?`.
- No behavior change to the board TUI or `board` text renderer.

## Implementation

- **Fallback at the CLI, not the skill.** `cmd_status`/`cmd_show` probe
  `_is_change(root, name)` first, then `os.path.isfile(_epic_path(root,
  name))`. Rejected: routing in the skill's SKILL.md prose — it would
  duplicate resolution logic and other callers (the `shipd` dispatcher)
  would not gain the fallback. A name matching neither stays `?` from
  `status` (the master `status-cli` contract), and `show` keeps printing
  `<name>: ?`.
- **Single lane projection.** New pure `board_lane(state)` in
  `spec_status.py`: `archived`→`shipped`, `ready`→`ready`,
  `unplanned`→`unplanned`, anything else→`building`. `dashboard.py`'s
  `flow_lane` (dashboard.py:261) becomes a delegating wrapper (dashboard
  already imports `spec_status` as `ss`; the reverse import would be
  circular). Rejected: duplicating the mapping — drift between board and
  report.
- **State-only lanes** (oracle-settled; verified/epic-autopilot: "a card
  follows its on-disk state"): the report is a deterministic derivation from
  on-disk artifacts via the existing `_member_state_with_root`; four lanes
  only.
- **Report layout.** First line `<slug>: <status>` and the metadata
  (`Theme:`/`Initiative:`) lines are byte-compatible with today's
  `epic-show` — the autopilot skill reads that status line
  (skills/autopilot/SKILL.md:54). Then `shipped <n>/<m>` (n = members with
  state `archived`, m = all stub members), a blank line, and the lanes in
  board order `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED`, each printed as
  `<LANE> (<count>)` even when empty. Member rows are indented two spaces,
  `%-22s` slug then state then `risk <value>`, where the risk is the last
  rating cell of the epic stub-table row (`parse_epic_changes` ratings tuple;
  `?` when absent), plus ` [worktree]` when `_member_state_with_root`
  resolved the state from a hosting root other than the invocation root —
  mirroring the text board's marker.
- **`show`/`epic-show` share one renderer** (`_epic_report_lines(root,
  slug)`), so the fallback output and the epic verb output are identical by
  construction.
- **Risk:** existing tests assert the flat `<mslug>: <state>` member lines of
  the old `epic-show` (tests/test_spec_status.py:516, :686-740); they are
  updated to the lane-grouped format in the same change. Format consumers are
  model-read skills only — no script parses member lines.
