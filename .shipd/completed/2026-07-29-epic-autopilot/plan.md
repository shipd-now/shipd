# epic-autopilot
Status: verified
Epic: autonomous-delivery

## Idea

Every piece of the autonomous pipeline exists — the context gate,
the pipeline contract, the plugin worktree helper, the proven headless
resume loop — but nothing composes them: shipping an epic's members still
means a human driving every plan and build by hand. The epic's promise
("no user interaction once it has enough context") has no engine.

This change delivers the autopilot:

- A shared session-driver module extracted from the eval runner's
  grade-gated resume loop — one driving idiom, two consumers.
- `autopilot.py`, a deterministic stdlib driver: iterate a ready epic's
  unplanned members risk-ascending; per member, worktree via the plugin
  helper → headless `/s:plan` → `spec_gate.py` → headless `/s:build` →
  auto-merging PR — honoring the resolved `autonomous-pipeline` stage
  list (skips, replacements, custom steps).
- A three-strike fix loop on non-gate failures, then parking the member
  as needs-human with its resumable session id (`claude --resume <id>`
  reopens the exact conversation for HITL); gate rejections park
  immediately with no retries.
- A `/s:deliver <epic>` skill: preflight, run the driver, relay the run
  report.

### Non-goals

- No driving of the `research` or `epic` stages — they precede the human
  epic-approval gate; the driver covers plan → gate → build (+ custom/
  replaced steps around them).
- No parallel members — strictly sequential, one worktree/branch/PR each.
- No strict MCP tool enforcement: v1 surfaces a stage's `tools` bindings
  as prompt guidance to the driven session; hard binding comes later.
- No re-driving of `rejected` or otherwise in-flight members — they are
  reported, never touched.

Affected capabilities: `epic-autopilot` (added). Impact:
`plugins/s/skills/build/scripts/session_driver.py` (new),
`autopilot.py` (new), `evals/run.py` (refactored onto the shared module),
`plugins/s/skills/deliver/SKILL.md` (new skill), tests for each, plugin
version bump to 0.5.0 (new skill = minor).

## Implementation

- **Shared driver module.** `session_driver.py` (stdlib): `run_turn(...)`
  spawning `claude -p [--resume]` with cwd/timeout, and
  `drive(prompt, cwd, grade_fn, reply, max_resumes, timeout, runner=None)`
  looping turn → grade → resume, returning `(ok, session_id, failure)`.
  The `runner` seam makes it unit-testable without live sessions;
  `evals/run.py` refactors onto it with behavior unchanged.
- **Member selection.** Parse the epic stub table; candidates are members
  whose derived state is `unplanned` (via `spec_status` internals
  in-process); order by the stub Risk column ascending (low < medium <
  high), ties by table order. Everything else (rejected, draft, active,
  archived …) is reported under its state and skipped.
- **Stage execution over `resolve_pipeline(root)`.** Only the `plan`,
  `gate`, `build` registry stages plus `custom` entries between them are
  driven; `research`/`epic` entries are noted as pre-approval and
  ignored. Skipped stages skip; a `replace` runs its command (cwd =
  member worktree) instead of the built-in; `tools` bindings are appended
  to the session prompt as guidance with their declared fallbacks.
  Stage grades: plan → member dir exists, lint-clean, `Status: ready`;
  gate → `spec_gate.py` exit 0 (2 = park as rejected, no retry);
  build → change archived under `completed/` and `gh pr view` on the
  branch reports an open or merged PR.
- **Three-strike loop.** A failed stage (session error/timeout, grade
  unmet after `max_resumes`, non-zero custom/replacement command) re-drives
  that stage with the failure summary appended to the prompt, three
  attempts total; still failing → park the member as `needs-human`
  carrying stage, reason, and the last session id; the worktree stays;
  the run continues.
- **Run report.** JSON to stdout-adjacent file plus a human summary:
  shipped (PR URLs), parked-rejected, parked-needs-human (session ids),
  skipped (state), unreached (`--max-members`). At run end, if any member
  PR merged, run the epic-sync close-out in a fresh worktree exactly as
  the build skill's Phase 7 prescribes.
- **Knobs.** `--max-members N`, `--dry-run` (print member order +
  resolved pipeline, drive nothing), `--timeout` per session,
  `--max-resumes`; `--claude-bin` for tests. Defaults: unlimited members,
  1800s, 4 resumes.
- **`/s:deliver` skill** is thin: verify the epic exists at
  `ready`/`active`, show the roster and resolved pipeline, confirm the
  knobs with the user, run the driver in the foreground, relay the
  report, and point at `claude --resume <id>` for parked members.

Risks: nested agents inside headless `/s:build` sessions behave
differently from plan sessions (guard: stage-specific grades, generous
timeout default, the three-strike loop); runaway spend (guard: sequential
members, `--max-members`, dry-run first in the skill's confirmation);
report drift vs reality (guard: grades read only on-disk/`gh` state,
never session transcripts).
