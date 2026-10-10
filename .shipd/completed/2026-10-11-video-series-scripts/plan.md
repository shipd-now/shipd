# video-series-scripts
Status: verified

## Idea

Write a shared episode template, a series overview, and nine episode scripts for the shipd video series under `docs/tutorials/videos/`.

### Motivation

The nine-episode video series has a roadmap but no scripts, so whoever records it has no grounded narration or on-screen plan. The shipd site, which vendors `docs/`, has no tutorial pages to sit beside the videos.

### Details

- `docs/tutorials/videos/template.md` — the shared episode structure, written first.
- `docs/tutorials/videos/index.md` — the series overview: the three roadmap groups, the episode list, and the open-source/commercial boundary.
- Nine scripts, `01-core-loop.md` to `09-management-plane.md`, each built from the template.

Affected capabilities: `video-tutorials` (added). Impact: eleven new markdown files under `docs/`; no code, no engine, no dependency.

### Non-goals

- No website edit. The hourly docs-sync adopts the pages as hidden; a follow-up change in `shipd-now-website` adds a "Tutorials" section to `content/docs.manifest.json`.
- No recording, editing, or captioning of the videos themselves.
- No edit to any existing doc under `docs/`.

## Implementation

- **Home.** The files live in the shipd repo's `docs/tutorials/videos/`, not in the website. The website's `content/docs/` is a vendored snapshot that `scripts/sync-docs.mjs` rewrites, so a page written there is lost. Rejected: authoring in the website repo.
- **Authoring.** Write every file with `/s:document`: read `plugins/s/skills/document/references/standard.md`, then run `docs_lint.py` until clean, then walk the skill's self-review checklist.
- **Doc types.** `template.md` and every episode are `how-to` (cap 150 lines): an episode walks a viewer through one task on screen. `index.md` is `concept` (cap 100 lines). Rejected: `reference` for episodes — a script is a walkthrough, not a lookup table.
- **The episode template.** Every episode file carries these sections, in this order, and no others:
  1. `<!-- doc-type: how-to -->` on line 1, then `# Episode <N>: <title>`.
  2. `## Introduction` — three to five sentences: the problem the viewer has, what the episode shows, and who it is for.
  3. `## At a glance` — a two-column table with rows `Roadmap group`, `Runtime`, `Prerequisites`, `Commands shown`.
  4. `## Script` — one `### <start>–<end> <beat name>` subsection per beat, each holding an `**On screen:**` paragraph and a `**Narration:**` paragraph. Timestamps run contiguously from `0:00` to the runtime.
  5. `## Takeaways` — three dot-points.
  6. `## Next` — one sentence linking the next episode file; episode 9 links `index.md`.
  7. `## Sources` — links to the docs and specs that ground every claim.
- **`template.md` content.** A how-to titled "Write a video episode script": a numbered list of fill-in steps, one per section above, plus the skeleton inside one fenced `markdown` block so its placeholders never render as prose.
- **Runtime.** Five minutes per episode, four to six beats. Episode 4 uses the roadmap's spotlight beats exactly: 0:00–1:00, 1:00–2:30, 2:30–4:00, 4:00–5:00.
- **Grounding (Q1).** Each episode keeps its roadmap title and arc, but every claim and command matches shipd's documented behavior and glossary. The roadmap diverges in four places, and the scripts reword them:
  - Ep 4: an epic decomposes one feature into member changes over shared decisions; a PRD precedes the epic. `/s:epic-grill` plans every unplanned member, cross-checks the plans, asks one question agenda, and gates each member. The "retry logic, cache race, telemetry gap" beat shows as questions on that agenda.
  - Ep 5: the oracle answers one compact decision from the wiki before a human; the supersession gate stops a build whose plan newer merges already implement.
  - Ep 6: a workspace is a repo that manifests the member repos, projects, and wiki of one cross-repo job — not rule inheritance into sub-packages.
  - Ep 7: the member map and headless runs as `docs/workspaces/member-map.md` and `headless.md` describe them.
- **Source map.** Ep 1: `docs/getting-started.md`, `what-is-shipd.md`. Ep 2: `docs/cheatsheet.md` (`shipd worktree`), `AGENTS.md`. Ep 3: `docs/prd.md`, `guardrails.md`. Ep 4: `verified/shipd-epic`, `verified/shipd-epic-grill`. Ep 5: `docs/oracle.md`, `supersession-gate.md`. Ep 6: `docs/workspaces.md`, `workspaces/getting-started.md`. Ep 7: `docs/workspaces/member-map.md`, `headless.md`, `teams.md`. Ep 8: `docs/copilot-review.md`, `semantic-review.md`, `verified/ci-action`. Ep 9: the `shipd-app` repo README (read-only delivery dashboard).
- **Episode 4 beats.** The four beats carry the roadmap spotlight's content in order: 0:00–1:00 the "yes-man" assistant that agrees with any design; 1:00–2:30 `/s:epic` decomposes one feature (from its PRD) into three dependent member changes; 2:30–4:00 `/s:epic-grill` plans the members and asks one agenda — retry logic, a cache-invalidation race, a telemetry gap; 4:00–5:00 the answers rewrite the affected plans, every member is gated execution-ready, and the hand-off names `/s:autopilot`.
- **Roadmap groups.** Episodes 1–2 sit in Tactical execution, 3–4 in Spec authoring and pressure testing, and 5–9 in Verification and governance; each `At a glance` table names that group.
- **Episode 9 boundary.** The commercial episode states the boundary from the roadmap: episodes 1–8 are open source, and the management plane is commercial. It describes only what `shipd-app` ships today; roadmap items it lacks are named as direction, not as shipped features. The direction column lists the roadmap's four items: executive dashboards, cross-repo drift tracking for architecture, compliance reporting, and org-wide policy rollouts.

Risk: a script asserts behavior the docs do not state. Guard: every beat's claim traces to a `## Sources` link, and the executor reads that source before writing the beat.

## Questions and answers

### Q1: How closely do the scripts follow the roadmap wording?
- **Question:** The roadmap diverges from shipd's behavior (epics grouping PRDs, the oracle reading repo state, workspace rule inheritance). Options: (1) keep titles and arcs but ground every claim in shipd's documented behavior and glossary; (2) follow the roadmap verbatim. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The documentation standard gives each glossary term exactly one meaning across every shipd surface, so roadmap wording that misuses epic, workspace, or oracle cannot stand. Keeping titles and arcs is the planner's recommendation, bound by the same rule.
- **Cited:** verified/shipd-document, plugins/s/skills/document/references/standard.md

### Q2: Does this change also make the pages visible on the website?
- **Question:** Options: (1) shipd-repo docs only, with website visibility a follow-up change in shipd-now-website; (2) include the website manifest edit. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. One change is one worktree, one branch, one PR, and the skills-venn-diagram change kept its website work out of scope the same way. The hidden adoption means merging the docs first does no harm.
- **Cited:** AGENTS.md, completed/2026-09-13-skills-venn-diagram, queue q-docs-diagram-placement

## Readiness attestation

### Problem and motivation

The video series has a roadmap but no scripts, and the shipd site has no tutorial pages.

Evidence:

- `docs/` holds no `tutorials/` directory; the roadmap arrived in the request.
- `shipd-now-website/scripts/sync-docs.mjs` vendors `docs/` into the site.

### Scope and non-goals

Eleven new files under `docs/tutorials/videos/`; the website manifest and the recordings stay out.

Evidence:

- In scope: `docs/tutorials/videos/` (new).
- Out of scope: `shipd-now-website/content/docs.manifest.json`, settled by Q2.

### Affected capabilities and files

One new capability, `video-tutorials`, and eleven new markdown files.

Evidence:

- Capability `video-tutorials` (added); no master exists to modify.
- Files: `docs/tutorials/videos/template.md`, `index.md`, `01-core-loop.md` … `09-management-plane.md`.
- Runnable premise: `docs_lint.py docs/workspaces/teams.md` → exit 0, so nested docs lint like top-level ones.
- Runnable premise: `find docs -name '*.md' -not -path 'docs/retros/*'` lists six `docs/workspaces/` files, so the CI lint step (`.github/workflows/ci.yml:87`) recurses into new subdirectories.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Grounding against the roadmap: the oracle, Q1.
- Repo split: the oracle, Q2.
- Template sections, file names, doc types, runtime: investigation of the documentation standard and the roadmap.
