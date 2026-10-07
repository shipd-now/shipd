## 1. Build skill model policy

- [x] 1.1 [req: provider-neutral-model-down] In
      `plugins/s/skills/build/SKILL.md`, replace the frontmatter
      `description`'s "on the most powerful model, then delegate
      implementation to execution sub-agents on the tier below" with "on the
      session's model, then delegate implementation to execution sub-agents
      on a model one step down", rewrapping the folded lines.
- [x] 1.2 [req: provider-neutral-model-down] In the same file's intro
      paragraph, replace "running on the next tier down (the
      second-most-powerful model)" with "running on the model down (one step
      below yours)".
- [x] 1.3 [req: provider-neutral-model-down] Replace the "Model policy"
      block's heading line and its first three bullets (through "not fixed
      names.") with the five bullets in `plan.md`'s `## Implementation`
      "Model policy text" decision, headed
      `**Model policy — the whole point of this skill (provider-neutral):**`.
      Keep the `subagent_model` override bullet that follows.
- [x] 1.4 [req: interactive-pipeline-resolution] In that override bullet's
      table, replace the `tier-below` / `tier-two-below` cell with the exact
      text from `plan.md`'s "Table row" decision.
- [x] 1.5 [req: provider-neutral-model-down] Rename the Phase 3 heading to
      `## Phase 3 — Spawn execution sub-agents (model down)` and change its
      body's "`model` set to the **second-most-powerful** tier per the model
      policy above (one step below the orchestrator)" to "`model` set to the
      **model down** per the model policy above".
- [x] 1.6 [req: provider-neutral-model-down] In the verification step 4
      ("If anything fails, spawn a sub-agent ..."), replace
      "(second-most-powerful tier)" with "(model down)".
- [x] 1.7 [req: provider-neutral-model-down] In `## Operating rules`,
      replace "Most-powerful tier plans; the tier below executes. Never
      invert this." with "The session's model plans; the model down
      executes. Never invert this."

## 2. Autopilot in-session table

- [x] 2.1 [req: interactive-pipeline-resolution, provider-neutral-model-down]
      In `plugins/s/skills/autopilot/SKILL.md`'s "declared `model`" table,
      replace the `tier-below` / `tier-two-below` cell with the same text as
      task 1.4. Leave the detached-driver anchor paragraph unchanged.

## 3. Version

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      by one patch from the value on `main` at build time.

## 4. Verification

- [x] 4.1 [req: provider-neutral-model-down] Run
      `grep -niE 'fable|opus|sonnet|haiku|most-powerful|most powerful'
      plugins/s/skills/build/SKILL.md` and confirm no output.
- [x] 4.2 [req: provider-neutral-model-down] Run
      `grep -n 'tier-two-below' plugins/s/skills/autopilot/SKILL.md` and
      confirm the table row names no model.
- [x] 4.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3
      plugins/s/skills/build/scripts/spec_lint.py`; confirm both pass.
