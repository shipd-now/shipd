# autopilot-in-session
Status: verified
Theme: developer-experience

## Idea

Make `/s:autopilot` drive an epic with Agent-tool sub-agents inside the current
Claude Code session by default, keeping the headless `claude -p` driver as an
explicit `detached` opt-in.

### Motivation

`autopilot.py:294` drives every stage as a headless `claude -p` subprocess, and
`deliver-skill` mandates the skill "run the autopilot driver in the foreground" —
so invoking the skill interactively still hands the work to opaque subprocesses
you cannot see, answer, or steer, even though you are sitting right there.

### Details

- Add an in-session drive to `plugins/s/skills/autopilot/SKILL.md`: the skill
  itself loops over members, spawning one general-purpose sub-agent per pipeline
  stage.
- Make it the default; route to the existing `autopilot.py` run only when the
  invocation asks for a `detached` run.
- Take member ordering from `autopilot.py --dry-run`, which already computes it
  and drives nothing.
- Grade each stage from disk with the same conditions the Python driver uses,
  expressed through the public CLI.
- Emit per-member heartbeats so the delivery board shows the run live.

Affected capabilities: `epic-autopilot` (modified). Impact:
`plugins/s/skills/autopilot/SKILL.md` and the version bump in
`plugins/s/.claude-plugin/plugin.json`. No engine script changes.

### Non-goals

- No change to `autopilot.py`. The detached path — `drive_member`, `session_fn`,
  three-strike parking, session-id capture, the JSON run report — is untouched
  and stays the unattended mode.
- No parallelism. Members run one at a time in-session, as they do detached.
- No new agent type. Stages run on a general-purpose agent, not a new
  `am:driver` definition.
- No run-state file. Member state already lives on disk, so a re-invocation
  resumes naturally.
- No autopilot invocation from the board's per-card run action; that keeps
  calling the detached driver.

## Implementation

- **The loop lives in the skill, not in Python.** In-session, the orchestrator
  is the driver: it reads the member order, creates each worktree, spawns a
  sub-agent per stage, grades from disk, and moves on. Rejected: teaching
  `autopilot.py` to emit stages for the skill to pump — the driver runs as a
  subprocess and cannot reach the Agent tool, so that design buys a second
  protocol and a persisted run state for no behavioral gain.

- **The two modes are deliberately *not* semantically identical.** Every piece of
  `autopilot.py`'s failure machinery — three-strike retry, `needs-human` parking,
  session-id capture, `claude --resume` pointers — exists because no human is
  present. In-session a human is present, so a failed stage or a gate rejection
  **stops and asks the user** rather than parking. This is the substantive
  difference between the modes, not an omission.

- **Ordering is delegated, never re-derived.** The skill runs
  `autopilot.py <epic> --dry-run`, which already prints the risk-ascending member
  order and the resolved pipeline and performs no action. Re-implementing the
  ordering in prose would be a second source of truth that silently disagrees.

- **Entry stage per member mirrors the Python mapping.** `unplanned` → `plan`,
  `ready` → `build`; any other state is skipped and reported. This is the same
  mapping as `autopilot.py:646`'s `_ENTRY_STAGE`, so both modes skip
  already-satisfied stages identically.

- **Grades are the same disk conditions, read through the public CLI.** The
  Python grades (`autopilot.py:196-240`) translate exactly:
  | stage | passes when |
  | --- | --- |
  | plan | `spec_status.py status <member>` is `ready` **and** `spec_lint.py <member>` exits 0 |
  | build | a `completed/` entry ending `-<member>` exists **and** `gh pr view change/<member>` yields a URL |
  | review | the PR head's `semantic-review` status is `success` **and** `review_gate.py resolve --check` reports `unresolved=0` |
  Grading from disk rather than from the sub-agent's summary is what keeps the
  modes honest: a sub-agent claiming success does not pass the stage.

- **Stages run on a general-purpose sub-agent carrying the stage's own prompt.**
  The instruction text is the same shape `_stage_prompt` (`autopilot.py:330`)
  produces — "Run `/s:plan` for the change `<member>` …" — with the member's
  worktree as the working directory. Rejected: running stages inline in the
  orchestrator, which would spend the main context on one member and lose the
  isolation that makes a bad stage cheap to discard.

- **Board liveness reuses the per-build heartbeat.** `heartbeat.py`'s
  `build-start` / `build-stage` / `build-finish` are per-change verbs, so the
  in-session loop emits them around each member exactly as `/s:build` does. The
  run-level heartbeat stays internal to `autopilot.py`; in-session runs surface
  as a sequence of building members, which is what the board renders anyway.

Risk: the skill's loop and the Python driver could drift on the parts that
*should* match — entry-stage mapping and the grade conditions. Both are stated in
the delta spec as observable scenarios so a drift is a failing scenario, not a
silent divergence.
