# harness-agent-docs
Status: verified
Epic: harness-agents
Theme: developer-experience
Planned-at: d5fca031f32de27e60fb2fbfea87503b38cd8027
Gated-hash: 96646834444f

## Idea

Document the harness agent surface: extend `docs/customise.md`'s harness section
and add a reference recording what ships per harness, where it lands, and how to
add a harness.

### Motivation

A user can now receive `shipd-sub-agent`, `shipd-oracle`, and `shipd-validator`
from `shipd install` or `shipd harness add`, but no document names them or says
where each harness puts them, so the new surface is undiscoverable and the
"add a harness" path is unstated.

### Details

- `docs/customise.md`: the harness section names the agent files written beside
  the commands and links to the new reference.
- `docs/harness-agents-reference.md`: a new reference listing, per harness that
  declares `subagents`, the agent repo and user-global locations, the
  frontmatter each carries, the `shipd-<role>` ids, and the steps to add a
  harness.

Affected capabilities: `harness-registry` (modified). Impact: documentation
only; no code, no plugin version bump.

### Non-goals

- No code change: the registry, render, verb, and bodies members are shipped.
- No change to the harness-install documentation beyond the harness section.
- No tutorial or how-to; the reference is lookup material.

## Implementation

- **The reference is lookup material, one table per fact.** It opens with the
  doc-type marker, states what the agent surface is and that it is gated on the
  `subagents` feature, then gives the four declaring harnesses' locations and
  frontmatter in a table, the three `shipd-<role>` ids, and the `shipd harness
  add`/`install` verbs. The `customise.md` harness section gains a short
  paragraph and the link, staying a reference rather than growing a second
  copy of the table.
- **Authored through the documentation standard.** Both files carry the
  `<!-- doc-type: reference -->` marker and are checked with
  `docs_lint.py` before the change ships.
- **No version bump.** The change touches `docs/` alone, not `plugins/s/`, so
  the plugin version does not move.

Risk: none material — documentation only.

## Readiness attestation

### Problem and motivation

The agent surface ships but no document names it or says where each harness
puts the files, so it is undiscoverable.

Evidence:

- Epic `harness-agents` Changes table: the `harness-agent-docs` row.
- `docs/customise.md`'s harness section names the command surface only.

### Scope and non-goals

Two documentation files; no code and no version bump.

Evidence:

- In scope: `docs/customise.md`, `docs/harness-agents-reference.md`.
- Out of scope: the engine and the plugin's other docs.

### Affected capabilities and files

One capability, `harness-registry`, modified; two documentation files.

Evidence:

- Capability `harness-registry`: `agent-surface-docs` added.
- Files: `docs/customise.md` (the harness section),
  `docs/harness-agents-reference.md` (new).
- Runnable premise: `python3
  plugins/s/skills/document/scripts/docs_lint.py docs/customise.md` → exit 0.

### No open task-shaping decision

Every task-shaping decision is settled by the epic and the shipped surface.

Evidence:

- The two files and their content: settled by the epic's Changes table.
- The doc-type and shape: settled by the documentation standard and the
  existing reference docs.
