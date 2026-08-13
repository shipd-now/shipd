# modal-worktree-artifacts
Status: verified

## Idea

Resolve the spec-detail modal's artifact tabs from the member's worktree-aware
location, so a change planned (or archived) inside its own worktree shows its
Plan/Spec/Tasks instead of "not yet planned".

### Motivation

The board already derives a member's state worktree-aware (`member_board_state`
probes `.worktrees/<slug>` and records the hosting directory as `location`),
but `MemberDetailScreen` resolves artifacts with `change_artifacts(app.root,
slug)` — the invocation root only — so a member mid-build in its worktree shows
"not yet planned — no spec files" despite carrying a full artifact set.

### Details

- `MemberDetailScreen` resolves artifacts from the member's `location`
  (falling back to the app root when absent), reusing `change_artifacts`
  unchanged.

Affected capabilities: `delivery-dashboard` (added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `change_artifacts` itself — its planned-then-completed
  resolution and dependency-free contract stand.
- No change to the epic-detail modal: epics live under the root's
  `epics/` directory, which has no worktree variant.
- No cross-worktree *listing* — only the already-known hosting directory is
  consulted.

## Implementation

- **Reuse the existing seam.** `member_board_state` already returns the
  absolute hosting directory and `_member_rows` stores it as
  `member["location"]`; the modal passes
  `member.get("location") or self.app.root` into the unchanged
  `change_artifacts`. Rejected: re-probing worktrees in the modal — the board
  aggregation already did that work.
- `change_artifacts` resolves the content dir from whatever root it is given
  (`sc.specs_dir`), so a worktree with its own layered config still resolves
  correctly.
- **Risk**: a stale `location` (worktree removed between refresh and click)
  degrades to the existing empty-artifacts notice — `change_artifacts`
  returns `[]` for a missing directory, never raises.
