# harness-agent-registry
Status: verified
Epic: harness-agents
Theme: developer-experience
Planned-at: 59a4352a138c3b16c0a9d650f557a78c88f8d270
Gated-hash: a2bb4a92f2d1

## Idea

Give the harness registry an agent surface: a neutral agent-definition source
for the three shipd roles, and per-harness agent targets and dialects for the
four harnesses that declare `subagents`.

### Motivation

A user on OpenCode, Antigravity CLI, or oh-my-pi runs `/s:build` and is told to
delegate to `shipd-sub-agent`, which nothing creates, because the registry
declares no agent target and no neutral agent source exists. The generator
member that renders the agents cannot be written until this data and source
land.

### Details

- `plugins/s/harness/agents/{sub-agent,oracle,validator}.md`: the neutral
  agent source, one file per role, opening with a
  `<!-- description: ... -->` marker and carrying the plugin's existing agent
  prose verbatim.
- `harness_registry.py`: `AGENT_DIALECTS`, `AGENT_ROLES`, a per-entry `agent`
  member (target paths, dialect, frontmatter fields, extra fields) for
  `claude-code`, `opencode`, `agy`, and `oh-my-pi`, and an `agent_surface(id)`
  accessor.
- `test_harness_registry.py`: `ENTRY_KEYS` gains `agent`; agent-field
  invariants and the four researched agent targets are pinned.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `harness-registry` (modified). Impact: no new
dependency; the eleven harnesses that declare no `subagents` carry no agent
surface and are otherwise unchanged.

### Non-goals

- No generator: rendering the source through a dialect is the
  `harness-agent-generate` member.
- No change to `plugins/s/agents/*.md`; pinning them to the claude-code render
  is the generate member.
- No install or `harness` verb writes; that is the `harness-agent-verb`
  member.
- No new feature in the `FEATURES` vocabulary and no new command surface.

## Implementation

- **The agent surface is declared data, like everything else in the registry.**
  Each `HARNESSES` entry gains one `agent` member: `None`, or a dict carrying
  exactly `repo_pattern`, `user_dir`, `dialect`, `frontmatter`, and `extra`.
  Presence is a single `None`-check, and the entry's top level stays the shape
  the existing invariants pin. Rejected: flat `agent_*` keys — they scatter one
  surface across five keys and make "has an agent surface" five separate checks.
- **An agent surface is exactly what `subagents` implies.** A non-`None` `agent`
  member is present if and only if the entry declares `subagents`, so the four
  declaring harnesses carry one and the other eleven carry `None`. The invariant
  is enforced in both directions by a test, so a future harness that turns the
  feature on without an agent target fails loudly.
- **The neutral source reuses the bodies' marker dialect.** Each
  `plugins/s/harness/agents/<role>.md` opens with
  `<!-- description: <one line> -->`, then the role's system-prompt prose, with
  no harness frontmatter. One template dialect covers both surfaces, the render
  step stays a small line-scanner with no YAML dependency, and the
  `harness-command-bodies` reader is the pattern to follow. Rejected: real YAML
  frontmatter in the source — it buys nothing the dialect needs and adds a
  parser to a stdlib-only engine.
- **The source is the existing prose, re-homed.** Each file's body is the
  plugin agent's body verbatim (`plugins/s/agents/<role>.md` minus its
  frontmatter), and a test asserts the two bodies match, so the neutral source
  cannot silently diverge from the Claude agents it is the source of. Rejected:
  a distilled rewrite — a second prose variant to keep in sync for no gain.
- **The four agent targets come from vendor documentation, pinned by tests.**
  `claude-code` `.claude/agents/shipd-{agent}.md` / `~/.claude/agents/` with
  `name`, `description`; `opencode` `.opencode/agents/shipd-{agent}.md` /
  `~/.config/opencode/agents/` with `description` plus `mode: subagent`; `agy`
  `.agents/agents/shipd-{agent}.md` / `~/.gemini/config/agents/` with `name`,
  `description` plus `subagent: true`; `oh-my-pi` `.omp/agents/shipd-{agent}.md`
  / `~/.omp/agent/agents/` with `name`, `description`. The `extra` tuple carries
  the constant fields (`("mode", "subagent")`, `("subagent", "true")`) the
  renderer emits verbatim after the `frontmatter` fields.
- **Accessors mirror the existing pair.** `agent_surface(id)` returns the
  entry's `agent` member or `None`, alongside `get(id)` and `ids()`.
- **The version bump rides here.** This change touches `plugins/s/`, so
  `plugins/s/.claude-plugin/plugin.json` moves `0.6.320` → `0.6.321` in the
  same PR.

Risk: the agent-target research for `agy` and `oh-my-pi` rests on vendor docs
rather than a locally installed harness; the pinned tests make a wrong path a
loud failure to fix in one place, and no rendering depends on it yet.

## Readiness attestation

### Problem and motivation

Every `subagents` harness but Claude Code is told to delegate to an executor
that no adapter can produce, and the generator member has no agent targets or
source to render until this data lands.

Evidence:

- Epic `harness-agents` Introduction: OpenCode, Antigravity CLI, and oh-my-pi
  "declare `subagents` and are told to spawn an executor that does not exist".
- `harness_registry.py` `HARNESSES`: four entries declare `subagents`; no entry
  carries any agent target today.

### Scope and non-goals

Registry agent data, the neutral source, their tests, and the version bump;
rendering, the plugin agents, and verb writes stay out.

Evidence:

- In scope: `plugins/s/harness/agents/*.md`, `harness_registry.py`,
  `test_harness_registry.py`, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: the epic assigns rendering to `harness-agent-generate` and verb
  writes to `harness-agent-verb`.

### Affected capabilities and files

One capability, `harness-registry`, modified; three new source files and two
edited files.

Evidence:

- Capability `harness-registry`: `registry-data` (base 8a5c7cad4a11) modified,
  `registry-agent-source` added.
- New: `plugins/s/harness/agents/sub-agent.md`, `oracle.md`, `validator.md`.
- Edited: `plugins/s/skills/build/scripts/harness_registry.py`,
  `plugins/s/skills/build/tests/test_harness_registry.py`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/build/tests -p 'test_harness_registry.py'` → exit 0, 26
  tests OK; the bodies suite → 27 tests OK.

### No open task-shaping decision

Every task-shaping decision is settled: the three design choices by the user,
the rest by the epic and the repository's existing patterns.

Evidence:

- Source format, registry field shape, and source content: settled by the user,
  Q1 through Q3.
- The `subagents`-gates-the-surface rule and the `shipd-<role>` ids: settled by
  the epic's Decisions.
- Accessor shape, the marker dialect, and the version bump: settled by
  investigation against `harness_registry.py`, `harness_bodies.py`, and
  `AGENTS.md`.
