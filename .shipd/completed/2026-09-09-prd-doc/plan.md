# prd-doc
Status: verified
Epic: prd-discovery

## Idea

Add `docs/prd.md`, the user-facing guide to the discover phase: what a PRD
is, where it lives, its lifecycle and templates, the `/s:prd` interview, and
how retrieval and the epic link tie it into delivery.

### Motivation

The whole PRD system is shipped — store, templates, emit, search, epic link,
and the `/s:prd` skill — but no user-facing documentation exists; a newcomer
has to reverse-engineer the discover phase from skill prose and specs.

### Details

- One standalone guide at `docs/prd.md`, mirroring the `docs/oracle.md`
  precedent (a topic page pinned by its owning capability's requirement).

Affected capabilities: `shipd-prd` (added requirement). Impact: the new
`docs/prd.md` only — nothing under `plugins/s/`, so no plugin version bump
(the bump rule is scoped to `plugins/s/`). No dependencies.

### Non-goals

- No edits to the workspaces guide, README, or cheatsheet — each is pinned
  by its own requirement (`workspaces-doc`, `project-readme`) and cross-links
  can be added later as their own change; `docs/oracle.md` sets the
  standalone precedent.
- No skill or engine changes.

## Implementation

- **Structure of `docs/prd.md`** (binding outline; write to the register and
  density of `docs/oracle.md` and `docs/workspaces.md`):
  1. `# PRDs` title, then the concept in two short paragraphs: the discover
     phase captured as an artifact; the hierarchy
     Initiative → PRD → Epic → Change with every link optional. Include a
     small mermaid diagram of that hierarchy with the PRD's links labeled
     (optional `Initiative:` upward in its own header, `PRD: <slug>` cited
     downward by epics).
  2. **Where a PRD lives**: the workspace, not the repo —
     `<workspace-root>/.shipd/prds/<slug>/prd.md` beside `initiatives/`;
     resolution walks the workspace chain (nested workspaces inherit the
     outer chain's PRDs); no workspace → no PRD, and `shipd workspace init`
     is the fix. State plainly that a PRD is standalone: it needs no
     initiative and no epic, ever.
  3. **Lifecycle**: `draft` → `approved`, or `superseded`; authored at
     `draft` by `/s:prd`; approval is a re-install of the edited file with
     `Status: approved` through the engine's staged emit with `--replace`
     (validation and restore-on-failure included) — never a hand edit of the
     store.
  4. **Templates**: the three tiers with their exact section lists (basic:
     Problem, Solution, Success criteria; standard adds Users, Requirements,
     Non-goals; comprehensive adds Risks, Rollout, Open questions),
     additively nested so a mid-interview tier switch keeps answered
     sections; `standard` is the default; the lint contract in one sentence
     (exact level-2 headings are a floor — extra sections are fine).
  5. **The `/s:prd` interview**: a short walkthrough — preflight, the
     search-first investigation, the section-by-section grilling, install,
     and the `/s:epic` handoff. Frame it as the way PRDs get written; the
     skill's own contract stays the authority.
  6. **Finding PRDs**: `shipd search <terms>` surfaces `kind: prd` records
     beside code, specs, wiki pages, and initiatives — with one example
     invocation and a trimmed example block of output.
  7. **FAQ** closing section answering the three standing questions in
     brief: where is it stored, is it always tied to epics (no — epics cite
     it, not the reverse), can it exist by itself (yes).
- **Command convention**: every interactive command in the guide invokes the
  `shipd` binary (`shipd workspace init`, `shipd search`) or names a `/s:`
  skill — never a `spec_status.py`/`spec_emit.py` path (the docs convention
  `workspaces-doc` establishes); the staged-emit mechanics are described in
  prose with the skill as the actor.
- **Diagram style**: mermaid, emoji-free labels, no hard-coded colors —
  matching the repo's dark-mode-safe diagram conventions.
- **Accuracy floor**: every behavioral claim in the guide must match what
  shipped — the tier lists match `spec_common.PRD_TIER_SECTIONS`, the paths
  match `prd_path`, `workspace-show` is never credited with listing PRDs
  (only `search` lists them), and the `PRD:` epic line's CI-safe resolution
  is stated as lint-time behavior in a discoverable workspace.
- **Risk**: doc drift from future engine changes — accepted for prose (same
  posture as every other guide), with the spec requirement pinning the
  load-bearing coverage so the validator and future lint sweeps have a
  contract to check against.
