## 1. Contract tests

- [x] 1.1 [req: epic-grill-amend-gate] In
      `plugins/s/skills/build/tests/test_epic_grill_contract.py`, inside
      `EpicGrillContractTest`, add
      `test_ending_runs_the_preflight_before_handing_off` reading
      `plugins/s/skills/epic-grill/SKILL.md` and `plugins/s/harness/bodies/epic-grill.md` with
      `_read`, and asserting for each of `skill` and
      `" ".join(body.split())`: `"--preflight" in text`,
      `"hand off only when the preflight exits 0" in text`, and
      "list every `fail` line" in text (the backticks are literal). Add
      `test_descriptions_name_the_green_preflight` asserting
      `"on a green preflight"` is in `" ".join(skill.split())` restricted to
      the text before the first `# /s:epic-grill` heading (the frontmatter)
      and in the body's first line. Extend the module docstring with
      one sentence naming the preflight pins. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_epic_grill_contract` and observe the
      two new tests fail.

## 2. Skill surfaces

- [x] 2.1 [req: epic-grill-amend-gate] In
      `plugins/s/skills/epic-grill/SKILL.md`, change the frontmatter clause
      `hand off to /s:autopilot. Never builds.` to `hand off to /s:autopilot
      on a green preflight. Never builds.` Rewrite the `## Ending — hand off,
      don't build` section so that, after the per-member summaries paragraph
      (unchanged), a new paragraph headed **Run the launch preflight** says:
      run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py"
      <epic> --preflight` once, from the repository root, after the last
      gate and even when a member did not reach `ready`; under a
      `## Preflight` heading relay every `warn` and `fail` line and the
      closing `preflight:` line verbatim, never the `ok` lines; a `warn`
      line (drift, overlap-files, a `doctor:` relay) is information and does
      not block. Then state the branch in these words: "hand off only when
      the preflight exits 0" — close with the `## Summary` sentence stating
      how many members are planned and gated and that the preflight is
      green, then `/s:autopilot <epic>` alone on its own line (keep the
      existing fenced example); "otherwise list every `fail` line" under the
      `## Summary` sentence (relay the stderr text instead when the verb
      printed no rubric line), say the run is not launched, print the
      preflight command to re-run after the remedies, and print no
      `/s:autopilot` line. Keep the closing never-build and interruption
      paragraph unchanged.
- [x] 2.2 [req: epic-grill-amend-gate] In
      `plugins/s/harness/bodies/epic-grill.md`, change the first-line
      description marker to end `... then reconcile and gate the plans
      together and hand off to /s:autopilot on a green preflight.` Rewrite
      step 7 as: `7. **Preflight and hand off.**` — after the last gate run
      `python3 "$S/autopilot.py" <slug> --preflight` once from the
      repository root; relay every `warn` and `fail` line and the
      `preflight:` line; print a why-first summary per member, any
      epic-wide answers and shared-requirement pairs, then a `## Summary`
      heading with one sentence stating the preflight verdict; hand off
      only when the preflight exits 0 by printing `/s:autopilot <slug>`
      alone on its own line; otherwise list every `fail` line (or the error
      text when no rubric line printed), name the preflight command to
      re-run, and print no hand-off. Never build. Keep the body under the
      `body-content` ceiling.
- [x] 2.3 [req: epic-grill-amend-gate] Run `python3 -m unittest
      plugins.s.skills.build.tests.test_epic_grill_contract
      plugins.s.skills.build.tests.test_harness_bodies` and confirm every
      test passes, including the new ones from 1.1 and the rendered-body
      line ceiling.

## 3. Version and verification

- [x] 3.1 [req: epic-grill-amend-gate] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch above the
      value on `main` at build time (`0.6.293` when this plan was written;
      rebase and re-bump if a sibling member landed first).
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests` from the worktree root and confirm every test passes;
      then read `plugins/s/skills/epic-grill/SKILL.md`'s `## Ending` and
      `plugins/s/harness/bodies/epic-grill.md` step 7 side by side and
      confirm both run the preflight once after the last gate, hand off only
      on exit 0, and list the `fail` lines otherwise.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 60 | 700 |
| (no tool) | 0 | 330 |
| Read | 1 | 138 |
| ToolSearch | 1 | 97 |
| Agent | 3 | 32 |
| SubagentHandback | 2 | 29 |
| **Total** | 67 | 1.3k |
