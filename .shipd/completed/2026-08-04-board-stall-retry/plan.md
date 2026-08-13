# board-stall-retry

Status: verified

## Idea

Surface stalled epics on the delivery board — a red ✗ before the epic's group
title and a warning-plus-Retry block in its epic-detail modal — and make the
retry actually work by teaching the autopilot to reclaim the stale worktree a
dead session leaves behind.

### Motivation

When driven sessions die on their first turn (e.g. token exhaustion), members
park `needs-human` with no session to resume, and the board shows nothing wrong
at the epic level. Worse, a re-run cannot heal itself: the dead run's leftover
worktree and branch make the autopilot's `worktree.sh <slug>` create step fail
with "already exists", parking the member again.

### Details

- A pure stall predicate over data the board already aggregates: an epic is
  **stalled** when its live heartbeat's run `state` is `finished` and at least
  one roster entry sits at `state: "needs-human"`. Gate-`rejected` members do
  **not** stall an epic — rejection is the normal enrichment park.
- Stalled epics render a `✗` marker (theme error color) before the slug in
  their group header title, and their epic-detail modal gains a warning block —
  one line per parked member (slug, stage, reason) — with a **Retry** button
  that dispatches the existing detached epic-level autopilot run.
- The autopilot's worktree stage reclaims stale leftovers: when create fails
  with "already exists", it runs the guarded `worktree.sh remove` (activity
  guard disabled, all other guards intact), deletes the merged-only branch, and
  retries create once; a guard refusal parks the member with the refusal as its
  reason.

Affected capabilities: `delivery-dashboard` (modified), `epic-autopilot`
(modified). Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/skills/build/tests/test_autopilot.py`, plugin version bump.

### Non-goals

- No change to the board's HTML page (`html` verb) — the stall signal is
  TUI-only.
- No per-member retry affordance in this change — Retry re-runs the epic-level
  autopilot, which re-selects exactly the still-unplanned/ready members.
- No resume of the dead sessions themselves — first-turn deaths recorded no
  session id; the existing `open` action already covers parked members that
  have one.
- No change to `worktree.sh` — the reclaim composes its existing guarded verbs
  from the autopilot side.

## Implementation

- **Stall predicate lives in `dashboard.py` as pure helpers.**
  `epic_stalled(epic)` returns whether the epic dict (as built by
  `build_board`) is stalled; `stalled_entries(epic)` returns its `needs-human`
  roster entries (each carrying `slug`, `stage`, `reason`). Both read only
  `epic["heartbeat"]`, need no `textual`, and are unit-testable like the other
  pure board helpers. Rejected: deriving stall from the last run report — the
  heartbeat is the live source the board already tails, and the report
  duplicates it.
- **Marker via `epic_group_title`.** The helper gains a `stalled=False` keyword
  and, when set, prefixes the title with `[$text-error]✗[/] ` (the registered
  shipd theme defines `error`, so the marker follows the theme — no hard-coded
  color, per the board-shipd-theme rule). `EpicGroupRow` measures titles with
  `Text.from_markup`, so control-offset math absorbs the marker unchanged. The
  lane-render call site (`_render_lanes`) passes `stalled=epic_stalled(...)`
  for the group's epic. Rejected: a separate marker widget — the title string
  is already the single source the offset math measures.
- **Repaint on stall flips.** `_lane_signature` currently folds in each card's
  entry `stage` but not its `state`, so a `needs-human` → `driving` flip (same
  stage) would repaint nothing and strand the marker. Add `entry.get("state")`
  to each card's signature tuple.
- **Warning + Retry in `EpicDetailScreen.compose`.** When the epic is stalled,
  render (after the header rule, before the member list) a warning `Static`
  reading `stalled: <n> member(s) parked needs-human` plus one line per entry
  (`<slug>  <stage>  <reason>`, `markup=False`), and a `Retry` button
  (`id="epic-retry"`). `on_button_pressed` for it calls
  `self.app.dispatch_epic_run(self.epic_slug)` then `self.dismiss()` — reusing
  the exact detached launch the run control's confirm dispatches. No extra
  confirmation: the warning block itself is the context, and the run is the
  same one the ▶ control offers. Non-stalled epics render no warning and no
  Retry.
- **Autopilot reclaim, error-driven.** In `drive_member`'s worktree step: when
  `command_fn([WORKTREE_SH, slug], root)` fails and its stderr contains
  `already exists`, run the reclaim sequence through `command_fn` (every step
  seam-visible and testable):
  1. If `.worktrees/<slug>` exists: `["env", "SHIPD_WORKTREE_IDLE_MINUTES=0",
     WORKTREE_SH, "remove", slug]` — the `env` prefix disables only the
     activity guard (a crash minutes ago always trips it) while the
     dirty/unshipped/claims guards stay in force. Non-zero → park
     `needs_human`, stage `worktree`, reason = the refusal output.
  2. If `["git", "show-ref", "--verify", "--quiet",
     "refs/heads/change/<slug>"]` exits 0: `["git", "branch", "-d",
     "change/<slug>"]` (merged-only delete — never destroys unmerged work).
     Non-zero → park with its stderr as reason.
  3. Retry `[WORKTREE_SH, slug]` exactly once; a second failure parks as
     today.
  Any create failure whose stderr lacks `already exists` parks unchanged — no
  reclaim attempt. Rejected: probing for leftovers before every create — the
  error-driven path keeps the common case at one seam call; the messages are
  this repo's own `worktree.sh` strings. Rejected: extending the `command_fn`
  seam with an env parameter — the `env` argv prefix needs no seam change.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` → `0.6.45`
  (`0.6.44` is claimed by the in-flight `plugin-0-6-44` worktree).

Risk: the reclaim keys on `worktree.sh`'s error text; if that wording drifts,
reclaim silently stops triggering and members park exactly as today — a safe
degradation, and `tests/test_worktree.py` pins the create-path messages.
