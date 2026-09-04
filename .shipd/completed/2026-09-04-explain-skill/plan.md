# explain-skill
Status: verified

## Idea

Add a read-only `/s:explain` skill that reads a shipd epic through the engine
and explains it in under 100 lines of prose, plus a diagram only where one
genuinely clarifies the epic's structure.

### Motivation

An epic's full picture spans a long `epic.md` (introduction, decisions, design,
member table) plus live member state, and the plugin has no quick read path
that condenses it — every existing epic surface (`epic-show`, the board) reports
status, not meaning. The user asked for `/s:explain`: a short explanation with
diagrams used sparingly.

### Details

- New skill `plugins/s/skills/explain/SKILL.md`, invoked as
  `/s:explain <epic-slug>`, modeled on the read-only contracts of
  `/s:memory` (engine-mediated reads, version banner) and `/s:duck`
  (strictly read-only, response-text output).
- Reads the epic through the engine: `spec_status.py cat epic <slug>` for the
  artifact and `spec_status.py epic-show <slug>` for live delivery state.
- A missing or unknown slug lists the available epics and stops.
- Registers the skill in the `AGENTS.md` roster and bumps the plugin version.

Affected capabilities: `shipd-explain` (added). Impact:
`plugins/s/skills/explain/SKILL.md` (new),
`plugins/s/harness/bodies/explain.md` (new — the `harness-command-bodies`
capability requires one body template per skill directory), `AGENTS.md`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No eval case under `evals/cases/` (the suite is plan-flow-focused today).
- No engine changes — the skill only consumes existing `spec_status.py` verbs.
- No epic mutation and no output files: the skill writes nothing, ever.
- No explanation surface for changes, initiatives, or research reports — epics
  only.

## Implementation

- **Read-only, response-text-only.** The explanation is printed as response
  text; the skill never writes a file or artifact (the `/s:duck` debrief
  precedent, `plugins/s/skills/duck/SKILL.md` "read-only — no exceptions").
  Rejected: writing an explanation file — it would need a home, a lifecycle,
  and cleanup for what is a conversational answer.
- **Engine-mediated reads.** Verified by running the commands: `cat epic
  personal-memory` exits 0 printing the full `epic.md`; `epic-show
  personal-memory` exits 0 printing status, lanes, and `shipped 5/5`;
  `cat epic no-such-epic` exits 1 with `Error: epic 'no-such-epic' not found`.
  The skill uses exactly these two verbs, run from the repo root.
- **Missing-epic fallback lists directory names, not the board.** On a missing
  or unknown slug the skill reports the engine's own error, then lists the
  available epic slugs as the child directory names of `<content-dir>/epics/`
  (content dir resolved via `spec_status.py config-show`, observed printing
  `content-dir: .shipd`). Rejected: the bare `show` board as the listing —
  observed that a selected change preempts the board (`show` printed
  `gate-trust-boundary: ?`), so it is not a reliable epic roster.
- **Budget semantics.** The 100-line ceiling covers prose lines only; fenced
  diagram blocks sit outside it. The skill treats 100 as a hard ceiling, not a
  target — a small epic gets a far shorter explanation.
- **Diagram policy.** A diagram appears only when the epic's structure (member
  dependency order, a pipeline, actor hand-offs) is faster read as a picture
  than as prose; permitted forms are swimlane-style ASCII or a mermaid block,
  the user's stated preference. A simple epic gets no diagram. Rejected:
  always emitting an architecture diagram — decorative visuals add length
  without carrying meaning.
- **Explanation structure.** The explanation covers, in order: what the epic
  is and why it exists (from `## Introduction`), the load-bearing decisions
  (from `## Decisions`), how the members compose (from `## Design` and the
  member table), and where delivery stands now (from `epic-show`'s lanes and
  shipped count).
- **Version banner.** Like every sibling skill, the first user-visible
  sentence announces `shipd:explain v<version>` read from
  `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.
- **Registration.** Skills are auto-discovered from
  `plugins/s/skills/<name>/SKILL.md`, so registration is the `AGENTS.md`
  roster sentence plus the mandatory plugin version bump
  (`plugins/s/.claude-plugin/plugin.json`, 0.6.174 → 0.6.175).
- **Harness body template.** The verified `harness-command-bodies` capability
  binds every `plugins/s/skills/<name>/` directory to one body template at
  `plugins/s/harness/bodies/<name>.md` (id sets must be equal — enforced by
  `plugins/s/skills/build/tests/test_harness_bodies.py`, which CI runs). So
  the change ships `plugins/s/harness/bodies/explain.md`: a distilled router
  (description marker first line, under 120 lines rendered, never a pasted
  SKILL.md) carrying **no `if:` gates** — the skill needs no subagents,
  dialogs, or file-references, and a gate-free body requires no
  `plugins/s/harness/references/explain.md` fallback and trivially avoids the
  empty-feature-render token bans.

Risk: an epic authored in a worktree and not yet merged is invisible to the
invocation root's `cat epic`; the skill mitigates by reporting the engine error
verbatim plus the roster of epics it *can* see, and stops rather than guessing.
