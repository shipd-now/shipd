## 1. Agent definitions, skill re-point, retirement

- [x] 1.1 [P1] [req: named-agent-types] Create `plugins/s/agents/sub-agent.md`:
      YAML frontmatter (`name: sub-agent`, a one-line `description` of the
      execution role, no `model:` key), body = the full role contract from
      `plugins/s/skills/build/references/subagent-prompt.md` generalized to be
      self-sufficient with no placeholders: it states that the orchestrator's
      spawn message supplies the change name, the absolute coordinator-script
      path, and optionally an "Orchestrator addenda" section that is binding;
      keep the loop, empty-claim/group semantics, truncated-TASK_TEXT note,
      no-guessing rule (release + `QUESTION:`), and all guardrails intact.
- [x] 1.2 [P1] [req: named-agent-types] Create `plugins/s/agents/validator.md`:
      frontmatter (`name: validator`, one-line adversarial-validation
      `description`, no `model:` key), body = the full role contract from
      `plugins/s/skills/build/references/validator-prompt.md` generalized the
      same way (spawn message supplies the change name only), keeping the
      inputs-and-only-these list, refute-don't-confirm posture, per-scenario
      verdict output contract, and guardrails.
- [x] 1.3 [P1] [req: artifact-compiled-context-handoff, orchestrator-addenda-slot, adversarial-validation-gates-verified]
      In `plugins/s/skills/build/SKILL.md`: re-point Phase 3 to spawn with
      `subagent_type: s:sub-agent`, spawn message = change name + absolute
      coordinator path + optional addenda section, description
      `builder <n> · <change>`; re-point Phase 5's validation step to
      `subagent_type: s:validator`, spawn message = change name only,
      description `validator · <change>`; update the "Paths in this skill"
      list to name the two agent definitions instead of the two prompt
      templates and remove all template-building/substitution instructions.
- [x] 1.4 [P1] [req: artifact-compiled-context-handoff] Delete
      `plugins/s/skills/build/references/subagent-prompt.md` and
      `plugins/s/skills/build/references/validator-prompt.md` (`git rm`), and
      fix any other living reference to them EXCEPT in
      `plugins/s/skills/build/SKILL.md`, which task 1.3 owns (grep
      `plugins/am` and `am/` docs; archived changes and `openspec/` stay
      untouched).
- [x] 1.5 [P1] [req: named-agent-types] In
      `plugins/s/.claude-plugin/plugin.json`: bump `version` to `0.2.0`.

## 2. Verify

- [x] 2.1 [req: *] From the worktree root: run the full suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) — all
      green; parse both agent files' YAML frontmatter (python3 with a simple
      key check — `name`, `description` present, no `model` key) and confirm
      both bodies contain their role contract anchors (claim loop + QUESTION
      rule for sub-agent; refute posture + verdict contract for validator);
      `grep -rn "subagent-prompt\|validator-prompt" plugins/ am/ README.md
      AGENTS.md` returns no hits outside `am/completed/`; run
      `python3 plugins/s/skills/build/scripts/spec_lint.py custom-agent-types`
      and confirm exit 0.
