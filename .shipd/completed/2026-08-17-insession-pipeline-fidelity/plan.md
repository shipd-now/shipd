# insession-pipeline-fidelity
Status: verified
Epic: pipeline-hardening

## Idea

Make the in-session autopilot drive honor every resolved pipeline entry form —
`skip`, `replace`, `custom`, `tools`, and pre-approval stages — exactly as the
detached driver does, and state the sub-agent → orchestrator reporting
contract in the build and autopilot skills.

### Motivation

The in-session drive (the default mode) hardcodes the plan/gate/build/review
loop and ignores `skip`, `replace`, `tools`, and `custom` entries, so the
shipped `basic` preset skips the gate under the detached driver but silently
still runs it in-session. The same audit found stage sub-agents ending turns
with their outcome pending on background watches the orchestrator never sees.

### Details

- `plugins/s/skills/autopilot/SKILL.md`: the in-session drive walks the
  resolved entry list (from `pipeline-show --json`, already consumed there)
  per member and honors each entry form — skip → not run, replace/custom →
  command run in the worktree, tools → instruction suffix, `research`/`epic` →
  noted and ignored — with entry-stage slicing and command-entry grading.
- `plugins/s/skills/build/SKILL.md` and the autopilot skill: state the
  reporting contract — a stage sub-agent that cannot message its parent ends
  its turn with the report as its final text; the orchestrator grades from the
  repository and never depends on a sub-agent's own background watch.
- `epic-autopilot` capability (modified): the in-session requirements gain the
  entry-form coverage the detached ones have, plus the reporting contract.
- `plugins/s/.claude-plugin/plugin.json`: version bump (standing convention —
  the change touches `plugins/s/`).

### Non-goals

- No new pipeline semantics: no new stages, options, presets, or grammar
  forms (epic non-goal) — a tool-only `replace` stays announced-and-skipped,
  mirroring the detached driver.
- No changes to `autopilot.py` or any engine script — the detached driver
  already honors every entry form; this is skill-and-spec work only.
- No renderer changes: the dry run stays the member-order source and its
  labels stay human-only.

## Implementation

- **The entry walk mirrors `drive_member`** (`autopilot.py:664-803`). Per
  driven member, iterate the `entries` array the run's single
  `pipeline-show --json` call produced, sliced to start at the first entry
  whose `stage` equals the member's entry stage (`unplanned` → `plan`,
  `ready` → `build`), mirroring `_pipeline_from_stage`
  (`autopilot.py:835-842`) — entries before the slice point, custom ones
  included, are already satisfied and are not run. Rejected: keeping the
  fixed stage list and special-casing forms around it — that is the bug being
  fixed.
- **Command entries run directly via Bash in the member's worktree**, not via
  a sub-agent — the same precedent as the gate entry, which the skill already
  runs directly. A `custom` entry runs its `command` at its list position; a
  `replace` entry's `command` runs in place of the built-in stage. Exit 0
  passes the entry; a non-zero exit invokes the existing in-session failure
  contract (stop and ask the user — never park), naming the member and the
  entry. A `replace` naming only a `tool` (no `command`) is announced and
  skipped, mirroring the detached driver's `[replace has no command;
  skipped]` (`autopilot.py:700-704`).
- **`skip: true` entries are announced and not run**; `research`/`epic`
  entries are noted as pre-approval and ignored (`PRE_APPROVAL_STAGES`,
  `autopilot.py:49`). By schema a skipped entry carries no other option, so
  no option handling applies to it.
- **`tools` bindings append the detached driver's verbatim suffix** to the
  stage instruction: a blank line then `Preferred tools for this stage, use
  when available: <name> (fallback: <fallback>); ...` — mirroring
  `_stage_prompt` (`autopilot.py:504-510`). Gate entries spawn no sub-agent
  in-session, so their `tools` have no instruction to decorate — same as
  detached, where only stage prompts carry the suffix.
- **Grading**: the existing per-stage grade table gains command-entry rows —
  a replace or custom entry is graded on the observed exit code of its own
  run, read directly by the orchestrator, never from a sub-agent summary.
  Heartbeat `build-stage` labels mirror the detached driver's: the stage name
  for stage entries, `custom:<name>` for custom entries.
- **The reporting contract lands in both skills.** In
  `autopilot/SKILL.md` (with "Grading a stage"): stage sub-agents cannot
  message the orchestrator mid-run — their report arrives as their turn's
  final text; the orchestrator grades from the repository and never waits on
  a process or watch a sub-agent left running in its own context. In
  `build/SKILL.md` (with Phase 7's watch): when this build runs as a driven
  stage sub-agent, run the PR watch to its terminal state in the foreground
  of the turn and end the turn with the Phase 7 report as the final text —
  never end the turn with the outcome pending on a background process, since
  no parent resumes a sub-agent for it.
- **Spec surgery on `epic-autopilot`**: MODIFY `in-session-drive` (base
  `3c0eda1eb8d9`) so the walk is entry-based ("one sub-agent per built-in
  stage entry it runs"); ADD `in-session-entry-forms` (the form table above
  as EARS requirements with scenarios mirroring the detached ones); ADD
  `in-session-reporting-contract`. Rejected: touching
  `pipeline-stage-execution` — the detached contract is already correct.
- **Runnable premise**: `spec_status.py pipeline-show --json` run in this
  worktree exits 0 and prints `{"source": "default", "entries": [...]}` with
  each entry dict carrying exactly its declared keys — the shape the walk
  consumes.
- Risk: skill-prose drift from the detached driver's semantics. Guard: every
  behavior above cites the `autopilot.py` line it mirrors, and the delta
  scenarios are near-copies of the detached requirement's scenarios, so the
  validator refutes divergence against the same contract.
