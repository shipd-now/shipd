# modal-live-artifacts
Status: verified

## Idea

Make the spec-detail modal live while a member is being driven: name the
in-flight stage in the empty-artifacts notice, and mount the artifact tabs the
moment the artifacts appear — without reopening the modal.

### Motivation

A member mid-plan shows the literal "not yet planned — no spec files" even
though the heartbeat knows a plan stage is running right now, and because the
modal resolves artifacts only once at compose time, artifacts emitted while
the modal is open stay invisible until it is closed and reopened.

### Details

- When no artifacts resolve but the member's heartbeat entry carries a live
  stage, the notice names it: `plan in progress (plan#1) — spec files appear
  once emitted`.
- The modal's existing 3-second refresh also re-resolves artifacts while the
  notice is showing, and swaps the notice for the tabbed artifact view when
  they appear.

Affected capabilities: `delivery-dashboard` (added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to artifact resolution rules (`change_artifacts` and the
  worktree-aware `location` fallback stand as shipped).
- No live re-render of *already-mounted* tabs when artifact files change on
  disk — only the notice→tabs transition is live.
- No notice change for a member with no live stage — the existing
  "not yet planned — no spec files" text stays for the genuinely idle case.

## Implementation

- **Stage-aware notice.** `MemberDetailScreen.compose` already holds the
  heartbeat `entry`; when `change_artifacts(...)` returns `[]` and
  `entry.get("stage")` is set, the notice widget (give it id
  `#artifact-notice`) renders `"%s in progress (%s#%s) — spec files appear
  once emitted"` (attempt omitted when absent, mirroring the header's
  stage#attempt formatting); otherwise the existing text. Pure formatting —
  factor it as `artifact_notice(entry)` in `dashboard.py`'s pre-textual
  stdlib zone (next to `change_artifacts`), covered through
  `test_change_artifacts.py`'s existing `_load_dashboard_stdlib()` loader.
- **Live mount.** The screen keeps one 3-second `set_interval` (started
  unconditionally now, not only when a session resolves). The handler does
  what it does today for activity, plus: while `#artifact-notice` is mounted,
  re-run the same `change_artifacts(location-or-root, slug)` resolution; on a
  non-empty result, remove the notice and mount the same `TabbedContent`
  structure `compose` would have built. Rejected: rebuilding the whole screen
  — it would drop scroll state and the activity chart's accumulation.
- **Risk**: mounting `TabbedContent` post-compose must land in the same
  container slot the notice occupied — anchor by mounting after/inside the
  notice's parent container, verified by the headless test.
