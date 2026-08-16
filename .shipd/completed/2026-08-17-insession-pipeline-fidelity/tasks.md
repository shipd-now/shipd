## 1. Autopilot skill — entry-form fidelity

- [x] 1.1 [req: in-session-drive] In `plugins/s/skills/autopilot/SKILL.md`,
      rework the in-session drive's stage sections into an entry walk: state
      that per driven member the drive iterates the `entries` array from the
      run's single `pipeline-show --json` call, sliced to start at the first
      entry whose `stage` matches the member's entry stage (`unplanned` →
      `plan`, `ready` → `build`), with every earlier entry — custom entries
      included — treated as already satisfied and not run (mirror
      `_pipeline_from_stage`, `autopilot.py:835-842`). Keep the dry run as
      the member-order source, unchanged.
- [x] 1.2 [req: in-session-entry-forms] In the same in-session section, add
      the entry-form handling: `skip: true` → announced, not run;
      `custom` → its `command` run via Bash in the member's worktree at its
      list position; `replace` with a `command` → that command run via Bash
      in the worktree in place of the built-in stage, no sub-agent spawned;
      `replace` naming only a `tool` → announced and skipped; `research` /
      `epic` → noted as pre-approval and ignored. Mirror the detached
      driver's semantics (`autopilot.py:664-711`) and keep the existing
      direct-run gate paragraph as-is.
- [x] 1.3 [req: in-session-entry-forms] In the same section, add the `tools`
      instruction suffix: a stage entry declaring `tools` appends a blank
      line then `Preferred tools for this stage, use when available: <name>
      (fallback: <fallback>); ...` to that stage's instruction, verbatim per
      `_stage_prompt` (`autopilot.py:504-510`); note that gate entries spawn
      no sub-agent so their `tools` decorate nothing.
- [x] 1.4 [req: in-session-entry-forms] Extend "Grading a stage" and the
      failure contract in `plugins/s/skills/autopilot/SKILL.md`: a command
      entry (custom or replacement) passes on the exit 0 the drive itself
      observed and, on non-zero, stops and asks the user with the member and
      entry named; heartbeat `build-stage` labels mirror the detached
      driver's (`custom:<name>` for custom entries, the stage name
      otherwise).

## 2. Sub-agent reporting contract

- [x] 2.1 [req: stage-subagent-reporting] In
      `plugins/s/skills/autopilot/SKILL.md`, alongside "Grading a stage",
      state the reporting contract: a stage sub-agent cannot message the
      orchestrator mid-run and ends its turn with its report as the turn's
      final text; the orchestrator grades from the repository (as already
      stated) and never waits on a process or watch left running in a
      sub-agent's own context.
- [x] 2.2 [req: stage-subagent-reporting] In
      `plugins/s/skills/build/SKILL.md`, next to Phase 7's watch (step 4),
      add the driven-stage note: when this build runs as a driven stage
      sub-agent, run the PR watch to a terminal state in the foreground of
      the turn and end the turn with the Phase 7 report as the final text —
      never end the turn with the outcome pending on a background process,
      because no parent resumes a sub-agent for it.

## 3. Version and verification

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump from the current
      value) — the change touches `plugins/s/`.
- [x] 3.2 [req: *] Verification barrier: run
      `python3 plugins/s/skills/build/scripts/spec_lint.py
      insession-pipeline-fidelity` (exit 0) and the stdlib suite
      `python3 -m pytest plugins/s/skills/build/tests -q` (green, no
      third-party installs), and re-read the two edited SKILL.md sections
      against `autopilot.py:664-803` to confirm the mirrored semantics
      match.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 76 | 23.0k |
| Edit | 13 | 9.1k |
| (no tool) | 0 | 7.4k |
| Read | 13 | 1.9k |
| Agent | 2 | 1.5k |
| SendMessage | 3 | 1.1k |
| Write | 1 | 944 |
| ToolSearch | 3 | 564 |
| **Total** | 111 | 45.5k |
