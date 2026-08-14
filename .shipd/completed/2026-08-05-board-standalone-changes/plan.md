# board-standalone-changes
Status: verified

## Idea

Surface standalone changes — those planned outside any epic — on the delivery
board, so a change being planned or built in its worktree is visible in its
lifecycle lane instead of invisible.

### Motivation

Every board card comes from an epic's stub table, so a standalone change
(no `Epic:` line, no stub row) never appears — a change mid-`/s:build` shows
"nothing building" on the board, which today hid five shipped fixes while
they were being built.

### Details

- The aggregation discovers standalone changes: the root's `planned/` plus
  every `.worktrees/*/` planned change whose plan carries no `Epic:` line
  and whose slug appears in no epic stub table, with worktree-aware state.
- Each lane renders them under a `standalone` group (epic and initiative
  modes; flat cards in `none` mode) — no run/open controls (both are
  epic-scoped), normal cards otherwise, so the spec-detail modal, worktree
  artifacts, and live activity all work unchanged.

Affected capabilities: `delivery-dashboard` (added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_change_artifacts.py` (or a sibling
stdlib test module), `plugins/s/skills/build/tests_textual/
test_dashboard.py`, `plugins/s/.claude-plugin/plugin.json`. No new
dependencies.

### Non-goals

- No autopilot integration: standalone changes have no epic heartbeat, no
  run control, and no board-dispatched runs.
- No stub-table or epic-file changes — membership stays exactly as authored.
- No discovery of completed archives that never had a worktree — a shipped
  standalone change leaves the board when its worktree is removed.

## Implementation

- **Discovery helper in the pre-textual stdlib zone** (`dashboard.py` before
  the `textual` import, next to `change_artifacts`):
  `standalone_changes(root, epic_member_slugs)` returns member-shaped dicts
  `{"slug", "description": "", "risk": None, "state", "location"}` for every
  change directory under `<content>/planned/` of the root and of each
  `.worktrees/<name>/` (the change named by the worktree dir), where the
  plan's header has no `Epic:` line and the slug is not in
  `epic_member_slugs`. State comes from the hosting root's plan `Status:`
  (falling back to `archived` for a completed archive, mirroring
  `_member_state` semantics); `location` is the hosting directory. Unreadable
  or malformed dirs are skipped, never raised. Covered through the existing
  `_load_dashboard_stdlib()` loader pattern.
- **Board shape**: `build_board` collects every epic's member slugs, calls
  the helper, and adds a top-level `"standalone": [...]` list (empty when
  none). Existing keys are unchanged, so current consumers are unaffected;
  `_annotate_member_actions` is not applied — standalone rows carry
  `"actions": []` and no session id (the modal's own resolution rules still
  apply once opened).
- **Lane placement** reuses `_member_column` with an empty heartbeat entry,
  so states map exactly as epic members do (`ready`→ready, `archived`→
  shipped, everything in-flight→building, `unplanned` never occurs since
  discovery only finds existing changes).
- **Rendering**: `_lane_contents` appends each standalone row to its lane
  under the pseudo-epic slug `standalone` (status `None`); in epic and
  initiative modes `_mount_epic_groups` renders that run as a group titled
  `standalone` with the usual count but **no run/open controls** (guarded by
  the pseudo-slug, mirroring initiative-mode headers); `none` mode renders
  the cards flat. Standalone content folds into the lane signatures the same
  way member rows do, so appearing/disappearing changes repaint.
- **Modal compatibility**: cards are ordinary `TaskCard`s with the
  member-shaped dict (`epic_slug="standalone"`), so `MemberDetailScreen`,
  worktree artifact resolution via `location`, the stage-aware notice
  (entry `{}` → idle notice), and the live-mount tick all work unchanged;
  the epic reference line names `standalone`.
- **Risk**: a worktree mid-creation could present a torn plan; the helper's
  skip-on-error posture covers it. A slug both standalone-planned and later
  adopted into an epic would double-render; the `epic_member_slugs`
  exclusion prevents exactly that.
