## 1. Contract test

- [x] 1.1 [req: deliver-skill, in-session-prebuild-drift, in-session-park-and-continue, in-session-unattended-prompts]
      Add `plugins/s/skills/build/tests/test_autopilot_skill_contract.py` in
      the shape of `plugins/s/skills/build/tests/test_epic_grill_contract.py`:
      `AutopilotSkillContractTest` reads `plugins/s/skills/autopilot/SKILL.md`,
      `plugins/s/harness/bodies/autopilot.md`, and `plugins/s/harness/references/autopilot.md`.
      Assert the skill text contains `--preflight`, `preflight:`, `the last
      question`, `spec_status.py" --root .worktrees/<member> drift <member>
      --base origin/main --json`, `git fetch origin main`, `git merge
      --no-edit origin/main`, `/s:drift <member> --base origin/main --json`,
      `verdicts[0].verdict`, `holds`, `revise`, `conflict`, `spec_gate.py
      <member> --base origin/main`, `--check`, `No human is available during
      this run`, `s:oracle`, `--outcome parked`, each reason token
      `grade-failed`, `gate-rejected`, `command-failed`, `sync-conflict`,
      `drift-error`, `drift-conflict`, `replan-failed`, `held by`, `gh pr view
      change/<dep> --json state`, `60 seconds`, `MERGED`, `CLOSED`, and
      `Parked`; that the skill text contains neither `ask, never park` nor
      `puts the situation to the user`; that the no-human sentence appears at
      least twice in the skill (plan and re-plan instructions); that the
      whitespace-normalized body contains `--preflight`, `fail`, `parks`,
      `drift`, and `Parked`; that the reference contains `## Pre-build drift
      step`, `park`, `held by`, and every reason token; and that
      `README.md`'s `/s:autopilot` row still exists. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_autopilot_skill_contract` and observe
      the failures.

## 2. The skill

- [x] 2.1 [req: deliver-skill] In `plugins/s/skills/autopilot/SKILL.md`
      Phase 1 (lines 52-79): make step 1 run `python3
      "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic>
      --preflight`, relay every line, and on any `fail` line stop — print the
      failing lines with their remedies, ask nothing, drive nothing; keep
      `epic-show`, `pipeline-show`, and the dry run as steps 2-4; state that
      a passed preflight means every driven member is `ready`, so the
      in-session drive's first `--waves` call returns build waves only. In
      Phase 2 (lines 81-121) add that the brief carries every `warn` line and
      that this confirmation is the last question of the run — after it the
      in-session drive never issues an AskUserQuestion or a typed round.
      Update the frontmatter `description` ("Preflights the epic" → "Runs the
      launch preflight, confirms the run controls as the last question") and
      the intro paragraph's "never ... answer a driven session's questions"
      to add "and after the confirmation never ask one".
- [x] 2.2 [req: in-session-prebuild-drift, in-session-unattended-prompts] In
      the same file, add a `### Pre-build drift step` section directly after
      `### Per-member setup` (line 218), written exactly as `plan.md`
      "Pre-build step" specifies: the trigger (first entry whose `stage` is
      `build`, once per member, before its `build-stage` heartbeat), the four
      numbered sub-steps with the sync commands, the drift verb invocation
      with `--root .worktrees/<member>` and `--base origin/main --json`, the
      exit branches, the verbatim **Drift instruction** block ("Run /s:drift
      <member> --base origin/main --json from this worktree and end your turn
      with that JSON object alone — no prose before or after it."), the
      `verdicts[0].verdict` read, the three verdict branches, the verbatim
      **Re-plan instruction** block (name the verdict's `revise:` pointer and
      reason, revise `planned/<member>/` in place, stay within the plan's
      `**Answered by:** USER` entries and the epic's Decisions, then run
      `spec_gate.py <member> --base origin/main`), the disk grade (`status`
      `ready`, `spec_lint.py` 0, `spec_gate.py <member> --check` 0), and the
      park reasons. Append the same no-human paragraph to the end of the
      **Plan stage instruction** block (line 280) and the re-plan block: "No
      human is available during this run. Put a decision the repository
      cannot settle to the oracle (spawn agent `s:oracle` with one compact
      question); on INSUFFICIENT adopt your recommended default and record it
      in the plan's ledger. Never open a question round or an
      AskUserQuestion." Reference the step from "Running a wave" step 2.
- [x] 2.3 [req: in-session-park-and-continue] In the same file, replace
      `### Failure contract: ask, never park` (lines 440-462) with `###
      Failure contract: park and continue`, written exactly as `plan.md`
      "Park and continue" and "Merge wait" specify: the reason vocabulary,
      the `heartbeat.py build-finish <member> --outcome parked` call, the
      in-flight-sub-agents-finish rule, the session-only parked set, the
      `git fetch origin main` before every `--waves` re-run, the drop of
      parked members, the held fixpoint over `blocked`/`waiting_on`, the
      skipped empty wave, and the bounded merge wait (`gh pr view change/<dep>
      --json state` every 60 seconds up to `--timeout`, `MERGED` → fetch and
      re-run, bound or `CLOSED` → end). Rewrite "Running a wave" step 6
      (lines 239-244) to say the re-run is filtered this way and that the
      drive stops only when no runnable wave remains and no dependency is
      being waited for. Rewrite `### The in-session run summary` (lines
      496-505) to the four groups — Shipped by wave with full PR URLs, Parked
      (member, reason, stage or step, resume pointer per the reference's
      table), Blocked (`held by <parked>` or `waiting on <dep>`, with the
      `/s:autopilot <epic>` re-run pointer), Skipped with state. Update
      `### Resuming an interrupted run` to say a parked member is re-driven
      from its on-disk state on re-invocation once its pointer's remedy is
      done, and the `deliver-skill` sentence about "answering a stopped stage"
      in the intro.

## 3. Harness body and reference

- [x] 3.1 [req: deliver-skill, in-session-park-and-continue] In
      `plugins/s/harness/bodies/autopilot.md`: make step 1's first paragraph
      run `python3 "$S/autopilot.py" <epic> --preflight`, relay its
      `ok|warn|fail` lines, and stop on any `fail` naming the remedies (keep
      the approval sentence as what the `epic-status` line checks); in step 2
      say the confirmation is the last question; rewrite the `<!-- if:subagents
      -->` paragraph in step 3 so the in-session drive runs a pre-build sync
      and drift check per member, re-plans a `revise` verdict without a human,
      and parks a failing member while carrying on with every member that does
      not depend on it; add to step 4 a `**Parked**` dot-point (reason, stage
      or step, pointer) and a `**Blocked**` dot-point. Keep `subagent`,
      `sub-agent`, and `AskUserQuestion` inside gates. Run `python3 -m
      unittest plugins.s.skills.build.tests.test_harness_bodies` and confirm
      the parity, forbidden-token, and ceiling tests pass with the body under
      150 rendered lines.
- [x] 3.2 [req: in-session-prebuild-drift, in-session-park-and-continue] In
      `plugins/s/harness/references/autopilot.md`: replace the `## Failure
      contract` section (lines 95-108) with the park-and-continue contract
      (reasons, wave finishes, held dependents, bounded merge wait); add a
      `## Pre-build drift step` section before it with the sync, the verb,
      the verdict branches, the re-gate, and a resume-pointer table —
      `gate-rejected` / `replan-failed` at `rejected` → `/s:plan <member>`;
      `grade-failed build` / `command-failed` / `sync-conflict` → `/s:build
      <member>` in `.worktrees/<member>` or re-run `/s:autopilot <epic>`;
      `grade-failed review` → the review post flow on the PR URL;
      `drift-conflict` → settle the named `Q<n>` or Decision (`/s:epic
      <epic> amend` for a Decision), re-gate, re-run; rewrite `## Resuming`
      (lines 110-118) to name re-invocation after the pointer's remedy.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      to the next patch above the value on `main` at build time (`0.6.293`
      when this plan was written; rebase and re-bump if a sibling member
      landed first). Re-run 1.1 until it passes.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests` from the worktree root and confirm every test passes;
      then run `python3 -c "import sys;
      sys.path.insert(0,'plugins/s/skills/build/scripts'); import
      harness_bodies as hb, harness_registry as hr;
      print(len(hb.render('autopilot', hr.FEATURES,
      refs_dir='/tmp/x').splitlines()))"` and confirm the count is below 150.
