# autopilot-close-out-fixes
Status: verified
Profile: lite
Theme: reliability

## Idea

Fix the two autopilot close-out defects observed in the mikk-knowledge
delivery run, and make the epic-close worktree self-cleaning.

### Motivation

The 2026-07-31 mikk-knowledge run showed the epic-sync close-out aborting on a
malformed CLI invocation and the report printing `-> claude --resume None` for
a member parked before any session existed. The close-out also always leaves
its `epic-close-<epic>` worktree behind.

### Details

- `_default_sync_fn` invokes `spec_status.py` with `--root` after the
  subcommand, which argparse rejects — the derivation silently never runs.
- `_summarize` unconditionally appends the resume pointer on needs-human
  lines, printing `None` when no session id exists.
- After a successful sync: remove the close-out worktree when the derivation
  was a no-op; name it in the output when a status change was written, so a
  human ships it.

Affected capability: `epic-autopilot` (modified). Impact:
`plugins/s/skills/build/scripts/autopilot.py`, its tests, plugin version.

### Non-goals

- No autopilot-authored epic-close PR — shipping a written status change stays
  a human step, per the protected-main workflow.
- No changes to member driving, parking, grading, or the report file schema.

## Implementation

- Reorder the close-out invocation to `spec_status.py --root <wt> epic-sync
  <epic>` (global flag before the subcommand — the form the build skill
  prescribes). Rejected: dropping `--root` and relying on cwd — explicit root
  keeps the call correct even if the cwd handling changes.
- In `_summarize`, print the needs-human resume pointer only when the entry
  carries a session id, mirroring the rejected branch's existing conditional.
- After a zero-exit sync, run `git status --porcelain` in the close-out
  worktree: empty → remove the worktree (`git worktree remove`) and delete its
  `change/epic-close-<epic>` branch; non-empty → print the worktree path with
  a ship-it-from-here pointer. A failed sync keeps the worktree for
  inspection, unchanged from today.
- Risk: cleanup adds git subprocess calls to the close-out path; guarded by
  routing them through the existing `_run_command` seam so tests fake them and
  a cleanup failure only prints (never raises).
