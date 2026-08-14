# custom-agent-types
Status: verified

## Idea

Execution and validator sub-agents are spawned as the built-in
`general-purpose` agent type, so the session's agents pane labels every worker
"general-purpose" — the reader can't tell an am builder from any other agent,
and the role prompt that defines these workers lives in markdown templates the
orchestrator must copy into every spawn. Claude Code plugins can define named
agent types (`agents/*.md`, registered as `<plugin>:<name>`), which fixes the
label and moves the role prompt to where the platform expects it.

- Add plugin agent definitions `plugins/s/agents/sub-agent.md` (registers as
  `s:sub-agent`) and `plugins/s/agents/validator.md` (`s:validator`); each
  body is the role's system prompt, generalized from today's
  `references/subagent-prompt.md` / `validator-prompt.md`.
- Re-point build's Phase 3 and Phase 5 to spawn those types, with a slim spawn
  message (change name, coordinator path, optional addenda) and role-labeled
  descriptions (`builder <n> · <change>`, `validator · <change>`).
- Retire the two prompt-template reference files.
- Bump the plugin version so the cache snapshot picks up the new agents.

### Non-goals

- Live per-task labels in the agents pane — a running agent's description is
  fixed at spawn; the platform offers no update mechanism.
- Changing the model policy, the claim loop, the no-guessing rule, or the
  validator's verdict contract — the prompts move, their content's meaning
  does not.
- Custom agent types for the orchestrator itself (it is the session, not a
  spawned agent).

Affected capabilities: `build-subagent-handoff` (modified + added requirement),
`build-spec-lifecycle` (modified: validator spawn). Impact:
`plugins/s/agents/` (new), `plugins/s/skills/build/SKILL.md`, deletion of
`plugins/s/skills/build/references/{subagent,validator}-prompt.md`,
`plugins/s/.claude-plugin/plugin.json`; snapshot refresh + new session needed
before the new types are spawnable.

## Implementation

- **Agent definition format:** markdown with YAML frontmatter (`name`,
  `description`); a file in the plugin's `agents/` dir registers as
  `am:<name>`. The body **replaces** the default system prompt entirely, so
  each definition must be self-sufficient: it keeps the full role contract
  (loop, no-guessing rule, guardrails / adversarial posture, output contract)
  from the template it absorbs.
- **No `model:` in frontmatter (binding).** The documented resolution order is
  env var → per-spawn `model` parameter → frontmatter → inherit. The
  orchestrator keeps passing the tier-below model per spawn; a frontmatter pin
  would silently fight the tier policy as models change. Rejected: pinning
  `opus` — wrong the day the orchestrator tier moves.
- **Parametrization via the spawn message, not the template.** The definitions
  contain no `<change-name>`/`<CLAIM_SCRIPT>` placeholders. Each body states:
  "the orchestrator's spawn message supplies the change name, the coordinator
  script path (builder) and any Orchestrator addenda; treat addenda as binding."
  Phase 3/5 spawn messages shrink to exactly those items. This keeps the
  addenda contract (`orchestrator-addenda-slot`) — the slot moves from a
  template section to a spawn-message section.
- **Spawn descriptions carry role + change:** `builder <n> · <change>` and
  `validator · <change>` (the description column is fixed after spawn — the
  two-word live-status idea lands as this, its best achievable form).
- **Templates are retired, not kept in sync:** `subagent-prompt.md` and
  `validator-prompt.md` are deleted in the same change; git history preserves
  them. Rejected: keeping them as "sources" for the agent bodies — two copies
  of a system prompt is exactly the drift this repo's specs exist to prevent.
- **Version bump to 0.2.0** (new user-visible surface: agent types), satisfying
  the AGENTS.md rule that every `plugins/s/` change bumps the version in the
  same PR.
- **Verification limits:** agent types register at session start from the cache
  snapshot, so spawning `s:sub-agent` cannot be exercised inside this build.
  The verify barrier checks frontmatter validity, reference cleanliness, and
  suite health; the first post-merge build is the live acceptance, mirroring
  how the statusline and cutover changes were accepted.
