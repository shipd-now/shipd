# harness-agent-generate
Status: verified
Epic: harness-agents
Theme: developer-experience
Planned-at: 4b6aee658a8884ad0f7dc477a01600568062d66f
Gated-hash: 22587795c734

## Idea

Add the generator's agent render path: compose a neutral agent definition with
a harness's agent dialect into the agent file's exact bytes, and pin the
checked-in Claude plugin agents to the claude-code render.

### Motivation

The registry now declares where each harness's agents land and ships the
neutral source, but nothing renders them, so the verb member has no bytes to
write and `/s:build`'s delegation still names an agent no harness receives. A
drift between the neutral source and the plugin's Claude agents is also pinned
only at the body today, not at the description.

### Details

- `harness_generate.py`: an `agent_source(role)` reader and a
  `render_agent(entry, role)` render path, plus the surface helpers
  `agent_repo_relpath`, `agent_user_basename`, and `agent_user_path`.
- `test_harness_generate.py`: the render contract per harness and the
  claude-code parity pin against `plugins/s/agents/<role>.md`.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `harness-verb` (modified). Impact: no new dependency;
a harness with no agent surface renders nothing.

### Non-goals

- No writing: `shipd install` and `harness add|remove|status` are the
  `harness-agent-verb` member.
- No change to the generated bodies or the Claude skills; naming the neutral
  ids there is the `harness-agent-delegation` member.
- No new registry data and no change to the neutral source.
- No documentation.

## Implementation

- **The agent render mirrors the command render.** `render_agent(entry, role)`
  returns the frontmatter head, then the ownership `MARKER`, then the source
  body — the same shape `render` produces, so a generated agent is owned and
  recognisable exactly like a generated command.
- **The head carries the entry's declared fields plus its `extra`.** The
  `frontmatter` tuple drives the field order; `name` renders `shipd-<role>`,
  `description` renders the source's marker text, and each `extra` pair is
  emitted verbatim after them, every value through `yaml_scalar`.
- **The parity pin is the description and the body, not the bytes.** The
  generated file carries the ownership marker and names the agent
  `shipd-<role>`, while `plugins/s/agents/<role>.md` carries no marker and
  names it `<role>` (Claude exposes the plugin's agents as `s:<role>`), so
  byte-equality is impossible without renaming the plugin agents and breaking
  every `s:<role>` reference until the delegation member lands. The test
  renders the neutral source for claude-code and asserts the rendered
  description and body equal the plugin agent's — where drift would actually
  show. Rejected: renaming the plugin agents to `shipd-<role>` for
  byte-equality.
- **The source reader is tiny.** `agent_source(role, base_dir=None)` reads
  `plugins/s/harness/agents/<role>.md`, requires the opening
  `<!-- description: ... -->` marker, and resolves to `(description, body)`;
  it raises `ValueError` naming the file when the marker is missing or the file
  is absent, mirroring `harness_bodies`' refusals. No feature gates and no
  `{refs}` substitution — agent prose carries neither.
- **A harness with no agent surface renders nothing.** `render_agent` and the
  three path helpers resolve to `None` when the entry's `agent` member is
  `None`, so the verb member can iterate every harness safely.
- **The version bump rides here.** `plugins/s/.claude-plugin/plugin.json` moves
  `0.6.321` → `0.6.322`.

Risk: the `extra` fields (`mode: subagent`, `subagent: true`) are pinned by the
render tests but not yet exercised against a real harness install; the verb
member is where they first reach a user surface.

## Readiness attestation

### Problem and motivation

Nothing renders the neutral agent source, so the verb member has no bytes to
write and `/s:build`'s delegation still names an agent no harness receives.

Evidence:

- Epic `harness-agents` Introduction: the four `subagents` harnesses "are told
  to spawn an executor that does not exist".
- `harness_generate.py` renders command files only; it has no agent path.

### Scope and non-goals

The agent render path, its surface helpers, their tests, and the version bump;
writing, the bodies, and the skills stay out.

Evidence:

- In scope: `plugins/s/skills/build/scripts/harness_generate.py`,
  `plugins/s/skills/build/tests/test_harness_generate.py`,
  `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: the epic assigns writes to `harness-agent-verb` and the body
  and skill naming to `harness-agent-delegation`.

### Affected capabilities and files

One capability, `harness-verb`, modified; two edited files plus the version
bump.

Evidence:

- Capability `harness-verb`: `agent-rendering` added.
- Edited: `harness_generate.py`, `test_harness_generate.py`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/build/tests -p 'test_harness_generate.py'` → exit 0, 69
  tests OK.

### No open task-shaping decision

Every task-shaping decision is settled by the epic and by investigation of the
render engine; none needed the user.

Evidence:

- The render shape, the ownership marker, and the YAML escaping: settled by
  `harness_generate.py`'s existing `render` and `_yaml_head`.
- The parity pin's scope: settled by the ownership marker — byte-equality is
  impossible without a rename that breaks the skills, so the pin is the
  description and body.
- The agent ids, the `subagents` gate, and the member split: settled by the
  epic's Decisions and Changes table.
