# harness-agents
Status: ready
Theme: developer-experience

## Introduction

shipd's `/s:build` delegates implementation to sub-agents, and `/s:plan`,
`/s:ask`, and `/s:autopilot` spawn them too. The harness framework already
tells a harness that declares `subagents` to delegate — the generated
`/s:build` body carries an `if:subagents` branch — but nothing ever writes the
agent definitions that branch needs. Only Claude Code has them, because the
plugin ships `plugins/s/agents/*.md`; OpenCode, Antigravity CLI, and oh-my-pi
declare `subagents` and are told to spawn an executor that does not exist. So
delegation is Claude-only in practice, and every other harness silently falls
back to doing the work in one agent.

This epic adds an **agent surface** to the harness framework: the sibling of
the command surface. One neutral agent-definition source per shipd role, a
per-harness agent target and dialect in the registry, and a generator that
composes them — written beside the command files by `shipd install` and
`shipd harness add`.

Intended outcome: every harness that declares `subagents` receives
`shipd-sub-agent`, `shipd-oracle`, and `shipd-validator` in its native agent
location, dialect-correct, so `/s:build` delegates on all four; adding a fifth
is one registry entry plus its agent dialect, never a body rewrite.

Success criteria:

- `shipd install` and `shipd harness add` write the three agents into each
  `subagents` harness's native agent surface, idempotently, with the same
  ownership markers and `--force` semantics as the command surface, and
  `harness status` reports them.
- A harness that declares no `subagents` gets no agent files, and its generated
  output is byte-for-byte unchanged.
- The checked-in Claude plugin agents equal the claude-code render of the
  neutral source, enforced by a test.
- The generated `/s:build` body and the Claude plugin skills name the neutral
  agent ids, and an OpenCode session running `/s:build` can delegate to
  `shipd-sub-agent`.
- All engine tests keep passing with neither `textual` nor `pydantic`
  installed.

### Non-goals

- **No new per-harness engine features.** Adapters render files only: no MCP
  servers, per-harness APIs, or network fetches — generation is local template
  rendering.
- **No change to the eleven harnesses that declare no `subagents`.** Their
  output is untouched; only the four declaring harnesses gain agents.
- **No port of the plugin's skill implementations.** The generated agents are
  distilled role definitions driving the `shipd` CLI, not copies of the `/s:`
  skills; the plugin stays the engine's distribution vehicle and the Claude
  Code authoring surface.
- **No per-harness model-tier configuration** beyond what a harness's agent
  dialect already supports.
- This epic does not itself plan or build its member changes.

## Decisions

- **The agent surface mirrors the command surface.** Registry entries gain
  agent fields — an agent repo pattern, a user-global agent directory, and an
  agent dialect carrying frontmatter fields and a mode — the generator gains an
  agent render path, and `shipd install` / `harness add|remove|status` write,
  remove, and report agent files exactly as they do command files. The whole
  surface is gated on the `subagents` feature already in the vocabulary, so a
  harness that does not declare it is untouched.
- **One neutral agent source; every harness renders from it.** The three roles
  (`sub-agent`, `oracle`, `validator`) live as neutral definitions under
  `plugins/s/harness/agents/`; the generator composes each with a harness's
  agent dialect. The checked-in Claude plugin agents are the claude-code render,
  pinned by a test, so the plugin-native agents and the generated ones cannot
  drift. Rejected: hand-kept per-harness copies (they drift), and generating
  only for the non-Claude harnesses (leaves Claude unproven by the pipeline it
  anchors).
- **Agent ids use the `shipd-` prefix.** `shipd-sub-agent`, `shipd-oracle`, and
  `shipd-validator`, mirroring `shipd-<command>` from `harness-install`. A
  dialect may reshape the id through an `{agent}` placeholder, but the neutral
  id is `shipd-<role>`.
- **Delegation names the neutral agents, in both surfaces.** The generated
  bodies' `if:subagents` branch and the Claude plugin skills' spawn text (build,
  plan, ask, autopilot) both reference the neutral agent ids, so the instruction
  and the agents it names come from one pipeline. Rejected: updating the bodies
  only (the Claude skills would keep pointing at a differently-named agent,
  reintroducing the split this epic closes).
- **Scope is the four declaring harnesses.** `claude-code`, `opencode`, `agy`,
  and `oh-my-pi` declare `subagents` today; the epic materializes agents for
  exactly those. Turning the feature on for a fifth harness is a registry edit
  plus its agent dialect, never a body rewrite.

## Design

The agent surface is the command pipeline's twin — one neutral source, per
harness dialects, two write surfaces:

```
harness/agents/<role>.md ──── one neutral definition per shipd role
      │  render(agent dialect)
      ▼
adapter registry ── per-harness agent target + dialect + declared features
      ├────────────▶ shipd install        (machine-level: user-global agent dirs)
      └────────────▶ shipd harness add    (per-repo: agent files beside commands)
```

The decomposition follows the same seams as `harness-install`: the neutral
source is content with no knowledge of dialects; the registry is data with no
knowledge of writing; the generator composes the two; the verb writes them; the
delegation member aligns the instructions that name them; the docs member
records the mode. Each member is independently testable under the stdlib-only
test suite.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| harness-agent-registry | The neutral agent-definition source under `harness/agents/` (sub-agent, oracle, validator) plus the registry's agent fields and agent-dialect vocabulary, with per-harness agent targets and dialects for claude-code, opencode, agy, and oh-my-pi, and their invariants and tests | medium | low | medium | low | |
| harness-agent-generate | The generator's agent render path: compose a neutral definition with a harness's agent dialect into the exact agent-file bytes, and the test that pins the checked-in Claude plugin agents to the claude-code render | medium | low | medium | low | harness-agent-registry |
| harness-agent-verb | `shipd install` and `harness add`/`remove`/`status` write, remove, and report the agent files beside the command files, with the same ownership markers, idempotent refresh, and `--force` semantics | medium | medium | low | medium | harness-agent-generate |
| harness-agent-delegation | The `if:subagents` branch of the generated bodies and the Claude plugin skills (build, plan, ask, autopilot) name the neutral agent ids, so the instruction and the agents it names ship from one pipeline | low | medium | low | medium | harness-agent-registry |
| harness-agent-docs | customise.md and a reference documenting the agent surface: what ships per harness, where it lands, and how to add a harness | low | low | low | low | harness-agent-verb, harness-agent-delegation |
