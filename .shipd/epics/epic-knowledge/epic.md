# epic-knowledge
Status: active
Theme: developer-experience

## Introduction

A feature accumulates far more knowledge than its epic can hold today:
strategy documents, meeting notes, API excerpts, decisions that arrive
mid-delivery, and facts that should outlive the feature entirely. The epic
currently admits exactly two reference kinds — research reports and video
briefs — so everything else either masquerades as a "research report",
lands only in a conversation transcript, or evaporates: the durable tier
(the wiki) is workspace-scoped and silently absent in most repos, which is
why oracle consultations routinely end `Queued: none` and typed decisions
are lost to the next session.

This epic adds the dossier layer around the epic without renaming it: a
general References shelf over a new engine-installed `docs/` artifact kind;
a capture rubric that tells every skill where arriving information belongs
— binding, reference, durable, or noise; a sanctioned amendment flow so an
epic's Decisions and shelf can accrete during delivery with the same
discipline as its status derivations; and a repo-local wiki fallback so the
durable tier exists everywhere.

Success criteria: a mid-delivery document can be installed and linked from
an epic in one engine-mediated step without pretending to be research; the
oracle never reports `Queued: none` in a shipd-initialized repo; and an
epic amendment ships as a lint-gated PR indistinguishable in discipline
from an epic-close derivation.

### Non-goals

- No renaming of the epic container — "epic" stays; this adds its dossier.
- No embeddings, search service, or retrieval infrastructure — the shelf
  and wiki stay grep-and-index markdown, matching the memory store.
- No migration of existing epics — `## Research` and `## Video` sections
  remain valid forever; `## References` is additive.
- No changes to the workspace wiki's chain semantics for repos that DO
  have a workspace — the fallback activates only where the chain is empty.
- No automatic capture — the rubric classifies; humans and skills decide.

## Decisions

- **One new artifact kind, `docs`, not per-purpose kinds.** Installed via
  `spec_emit.py docs <slug> --from <file>` into `<content-dir>/docs/<slug>/doc.md`,
  title-validated like research (no citation skeleton demanded), read back
  via `cat docs <slug>`, discoverable via `related` and `shipd list docs`.
  Rejected: distinct kinds per document flavor (notes, strategy, excerpt) —
  taxonomy lives in the document and the shelf annotation, not the storage.
- **`## References` is a superset section, not a replacement.** It accepts
  entries resolving under `research/`, `video/`, or `docs/`, with the same
  link-must-resolve lint as today's sections; `## Research` and `## Video`
  keep working unchanged so no existing epic or skill breaks. New authoring
  prefers `## References`.
- **The capture rubric is a reference document skills consult, modeled on
  `ask`'s capture rubric.** Four tiers with examples and tie-breakers:
  binding (changes what executors do → epic Decisions via amendment),
  reference (supports this feature → shelf), durable (outlives the feature
  → wiki via `/s:teach`), noise (recorded nowhere, deliberately). The
  plan/build/epic skills name the rubric at the moments information
  arrives: plan's question rounds, build's Q&A loop, epic authoring.
- **Amendment is a flow with engine guardrails, not a free edit.** The
  pattern mirrors epic-close: a fresh `epic-amend-<slug>` worktree, edits
  to Decisions/References only (Introduction and the stub table stay the
  decomposition's record; member rows change only through the existing
  status machinery), each amended Decision stamped with a dated provenance
  line, lint-gated, shipped as an auto-merging PR. The engine gains an
  `epic-amend-check` verb the flow runs before shipping: it diffs the epic
  against `main` and refuses when protected sections changed.
- **The wiki falls back to a repo-local store.** When the workspace chain
  is empty, wiki resolution lands at `<content-dir>/wiki/` in the repo
  itself — same layout, same queue, same lint — so `/s:teach`, `/s:ask`
  queuing, and oracle citation all work in a bare repo. When a workspace
  later appears, the chain takes precedence and the repo store becomes its
  nearest member's equivalent; a doctor line reports which store resolved.
  Rejected: requiring `/s:workspace init` first — knowledge capture must
  not be gated on infrastructure the pilot repos demonstrably skip.
- **Plugin version bumps ship with each member touching `plugins/s/`**, per
  AGENTS.md; skills reference the rubric by plugin-root path exactly as
  they reference `ask`'s today.

## Design

Three tiers, each with one home and one gate: binding knowledge lives in
epic Decisions and member plans, guarded by the amendment flow's
protected-section check; reference knowledge lives in the content dir's
`research/`, `video/`, and new `docs/` folders, reachable from epics and
plans through the `## References` shelf, guarded by staged emission and
link lint; durable knowledge lives in the wiki — workspace chain first,
repo-local fallback otherwise — guarded by the existing teach/queue
discipline. The capture rubric is the router standing at the boundary, and
the skills quote it rather than improvising.

Member seams follow the tiers: the `docs` kind is pure engine (emission,
read, list, lint); the shelf is grammar plus the two authoring skills; the
rubric is a reference document plus skill wiring; the amendment flow is a
skill flow plus one guard verb; the wiki fallback is resolution-layer only.
The `docs` kind lands first — the shelf links it, the rubric routes to it.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| docs-artifact-kind | `spec_emit.py docs` staged install into `<content-dir>/docs/`, `cat docs`, `related` and `shipd list docs` coverage, title lint | medium | medium | low | low |
| epic-references-shelf | Optional `## References` epic section accepting research/video/docs links with resolve-lint; `/s:epic` and `/s:plan` install-and-link arbitrary supplied documents through the docs kind | medium | medium | low | low |
| epic-capture-rubric | The four-tier capture rubric reference document plus consult wiring in the plan, build, and epic skills at their information-arrival moments | low | medium | low | low |
| epic-amend-flow | The `/s:epic <slug> amend` flow over a fresh `epic-amend-<slug>` worktree with dated Decision provenance, plus the `epic-amend-check` guard verb refusing protected-section edits | medium | medium | medium | medium |
| repo-wiki-fallback | Wiki resolution falls back to the repo's own `<content-dir>/wiki/` when the workspace chain is empty — teach, queue, and oracle citation all functional in a bare repo, with doctor and config-show reporting the resolved store | medium | high | medium | medium |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 223 | 46.0k |
| Edit | 40 | 8.6k |
| Read | 58 | 5.0k |
| Agent | 6 | 1.4k |
| SendMessage | 3 | 1.3k |
| ToolSearch | 4 | 599 |
| (no tool) | 0 | 574 |
| Monitor | 2 | 33 |
| Write | 1 | 3 |
| **Total** | 337 | 63.5k |
