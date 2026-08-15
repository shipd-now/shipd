# status-workspace-report
Status: verified

## Idea

Give `show` a workspace-level board report when it is invoked with no
argument and no spec is selected, so bare `/s:status` reflects the whole
delivery board instead of erroring.

### Motivation

`show` with no argument and no selection errors ("no change given and no
spec selected"), while the board's no-argument view is the whole workspace —
totals, every epic's members in lanes, standalone changes; the user expects
bare status to reflect what the board shows.

### Details

- `show` with no name and no selection prints the workspace board report:
  a `N specs · N epics · N initiatives` totals line, `shipped <n>/<m>`, and
  the four board lanes — member rows with an epic column in the non-shipped
  lanes, per-epic rollup rows in `SHIPPED`.
- Standalone changes (planned outside any epic) fold in under the epic
  column `standalone`; discovery relocates from `dashboard.py` into
  `spec_status.py`, with dashboard delegating (the `board_lane` pattern).
- `status` keeps its no-selection error — a bare status value has no
  workspace meaning. A selection, when present, still wins for `show`.
- The `/s:status` skill maps the no-argument invocation to `show` alone;
  plugin version bump.

Affected capabilities: `spec-status` (modified). Impact:
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/build/tests/test_change_artifacts.py`,
`plugins/s/skills/status/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.
No new dependencies — stdlib only.

### Non-goals

- No "shipped this week" figure — ship events belong to the delivery-metrics
  engine; this report derives from the spec tree alone.
- No change to the `status` verb's contract (bare value or error), and no
  change to `show <name>`'s change/epic behavior.
- No board TUI or `dashboard.py board` behavior change — the relocation is
  behavior-neutral for every dashboard caller.
- No heartbeat reads: state-only lanes, as in the epic report.

## Implementation

- **Fallback placement.** `cmd_show` checks `change is None/empty and
  read_current(root) is None` **before** `_resolve_change` (which raises on
  no selection) and prints `_workspace_report_lines(root)`; every other path
  through `cmd_show`, and all of `cmd_status`, is untouched. Rejected:
  changing `_resolve_change` itself — it serves `validate`/`set-status`/
  `sync`, which must keep erroring.
- **Relocate standalone discovery.** `_standalone_plan_path` and
  `standalone_changes` move verbatim from `dashboard.py` (dashboard.py:152,
  :169) into `spec_status.py` (their `ss.` self-references become local);
  `dashboard.py` keeps thin delegating wrappers with the same names and
  signatures, so `build_board` and `tests/test_change_artifacts.py`
  (which calls `dashboard.standalone_changes`) are unaffected. Rejected:
  a second discovery implementation in `spec_status.py` — drift; and
  importing dashboard from spec_status — circular (dashboard imports
  `spec_status` as `ss`).
- **Report layout.** Line 1: `N specs · N epics · N initiatives` mirroring
  `_board_totals_text` (dashboard.py:1426): specs = members summed across
  every epic (standalone not counted, matching the board header), epics =
  epic count, initiatives = distinct `Initiative:` slugs across epic files.
  Line 2: `shipped <n>/<m>` over every rendered row — epic members plus
  standalone entries — with `n` those whose lane is `shipped`. Blank line,
  then lanes in board order `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED`,
  each `<LANE> (<count>)` even when 0.
- **Rows.** Non-shipped lanes: `  %-20s %-22s %-12s risk %s%s` — epic slug
  (or `standalone`), member slug, state, risk (stub-table last rating cell;
  `?` for a missing cell and for standalone entries, whose member dicts
  carry `risk: None`), and ` [worktree]` when the state derived from a
  worktree (epic members via `_member_state_with_root`; standalone entries
  via their `location` differing from the invocation root). `SHIPPED`:
  per-epic rollup rows `  <epic-slug> (<n>)` in epic order, plus
  `  standalone (<n>)` last when any standalone change is archived —
  mirroring the board's collapsed per-epic shipped groups (oracle-settled;
  delivery-dashboard grouping requirement).
- **Lane derivation** stays `board_lane(state)` — the shared projection from
  the epic report; epics enumerated by globbing `epics/*/epic.md` under the
  resolved content dir, in sorted order, tolerating an unreadable epic file
  by skipping it (mirroring `_all_epic_member_slugs`'s fail-soft read).
- **Skill mapping.** `/s:status` with no argument runs `show` only — when a
  selection exists that prints the change one-liner (plus `status` for the
  bare value as today, guarded by the selection existing); with none it
  prints the workspace report, relayed verbatim.
- Risk: the report walks every epic's members through worktree probing
  (`_member_state_with_root`), so cost grows with epics × worktrees — fine
  at CLI scale (the board already does the same aggregation every 2s).
