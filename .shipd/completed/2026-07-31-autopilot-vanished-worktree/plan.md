# autopilot-vanished-worktree
Status: verified

## Idea

Make the autopilot survive a member worktree vanishing mid-run: resolve the
member's true outcome from its PR instead of crashing the whole run.

### Motivation

A driven `/s:build` session legitimately merges its PR and removes its own
worktree during close-out, after which the autopilot's next session turn
launches in the deleted directory and the run dies with an uncaught
`FileNotFoundError` — the member ships but the run records nothing and any
later members are never driven. This crashed both real runs of the
`autonomous-delivery` epic at the same spot.

### Details

- `session_driver.run_turn` returns a working-directory-missing turn failure
  instead of raising when its `cwd` no longer exists.
- `autopilot.drive_member` detects a vanished worktree (at each stage start
  and after a stage failure) and resolves the outcome from the repo root via
  the member branch's PR: merged → `shipped` (with URL, remaining stages
  skipped); not merged → `needs-human` with a worktree-vanished reason and
  the last session id. The run continues with the next member either way.

Affected capabilities: `epic-autopilot` (modified:
`shared-session-driver`, `pipeline-stage-execution`). Impact:
`plugins/s/skills/build/scripts/session_driver.py`,
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests/test_session_driver.py`,
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No change to what driven sessions do — removing their worktree at
  close-out stays legitimate; the driver tolerates it rather than forbids it.
- No worktree resurrection or re-creation mid-member.
- No change to gate semantics, three-strike counts, or the heartbeat.

## Implementation

- **Two seams, one behavior.** The turn runner (`run_turn`) only converts
  the crash into a normal turn failure — `except OSError` around
  `subprocess.run`, returning
  `(False, "working directory missing: <cwd>", None)`; classification stays
  out of the driver module. The outcome resolution lives in
  `drive_member`, which owns member state. Rejected: catching in
  `_three_strike` — it lacks the member/root context to resolve outcomes.
- **Detection points.** In `drive_member`'s pipeline loop: check
  `os.path.isdir(cwd)` (a) at the top of each entry iteration and (b) after
  any failed stage action, before parking. Either hit routes to a single
  `_resolve_vanished(root, slug, last_session_id)` helper. Retries inside a
  stage stay untouched — a vanished cwd makes each attempt fail fast (Popen
  raises before any session spawns), so the three-strike loop terminates
  immediately and costs nothing.
- **Outcome resolution.** `_pr_url` gains an explicit directory argument and
  is called with `root` (the main checkout — same repo for `gh`), never the
  possibly-deleted worktree; the end-of-pipeline call switches to `root`
  too. Merged PR → `MemberResult(outcome="shipped", pr_url=url,
  merged=True)`; anything else (no PR, open PR, `gh` failure) →
  `needs_human`, stage recorded as the stage in flight, reason
  `worktree vanished mid-run`, keeping `last_session_id` for
  `claude --resume`. Rejected: treating open-PR as shipped — an unmerged PR
  means the close-out did not finish; a human should look.
- **Seam guard stays.** The existing `command_fn is _run_command` guard on
  the final `_pr_url` call keeps fake-seamed tests offline; the vanished
  path uses the injected `command_fn` for the PR probe so tests can drive
  it (build the probe on `command_fn`, not on raw `gh`).
- **Tests** extend the existing fake-seam suites: `test_session_driver.py`
  drives `run_turn` at a nonexistent cwd (no crash, failure names the
  directory); `test_autopilot.py` simulates a build stage whose session
  removes the worktree — merged-PR probe → member `shipped` and the next
  member still driven; unmerged probe → `needs-human` with the
  worktree-vanished reason.
- **Version bump** — `plugins/s/.claude-plugin/plugin.json` to the next
  free patch above `origin/main` (0.6.5 → 0.6.6 as of planning).

Risk: the root-based `gh pr view` needs the branch name, which survives the
worktree removal (`change/<slug>` is deterministic), so resolution never
depends on the deleted directory. A network-less environment degrades to
`needs-human` — the conservative outcome — never to a crash.
