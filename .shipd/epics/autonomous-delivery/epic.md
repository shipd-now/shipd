# autonomous-delivery
Status: complete
Theme: developer-experience

## Introduction

Planning large features today starts from a blank page: the planner
investigates the repo well, but nothing gathers *external* context (prior
art, APIs, design trade-offs published elsewhere), epic authoring is manual,
every member change needs a human at the plan gate, and PR quality rests
entirely on the `ci` unit suite — there is no semantic review of what a
change actually does to the code's structure. The result is that extensive
features are slow to consider and expensive to shepherd.

This epic builds the autonomous delivery pipeline: a deep-research skill
turns a question into a cited report using the session's built-in web
tools; epic authoring consumes that report; and once a human approves the
epic, an autopilot plans and builds every member unattended — each member
plan passing an automated context-sufficiency gate (insufficient context
parks the plan as `rejected` for human enrichment instead of guessing), and
every PR gated by ci plus a CodeRabbit-style AST-aware semantic review.
The pipeline itself is configurable: stages can be skipped, replaced, or
extended per workspace or repo through the layered config convention.
Success: a user can take a feature idea through research → epic → merged
member PRs with exactly one approval (the epic) when context suffices, and
the only other human touchpoint is enriching a rejected plan.

### Non-goals

- No external research infrastructure: no Tavily keys, no local model
  endpoints, no embeddings sidecar — the session's built-in WebSearch and
  WebFetch tools are the whole search stack (the deep-research repo is
  architectural inspiration, not a dependency).
- No parallel member builds: autopilot runs members sequentially, one
  worktree/branch/PR each.
- No human-free epic approval: the epic gate stays human; autonomy begins
  after it.
- No replacement of the ci unit suite — semantic review is an additional
  required check, not a substitute.
- No silent weakening of the pipeline: gates disappear only through an
  explicitly authored pipeline definition or an explicit skip entry, never
  as an accidental side effect.

## Decisions

- **Built-in tools only for research.** The research skill orchestrates
  staged work (decompose → search → select → extract anchored findings →
  compose a cited report) in skill instructions over WebSearch/WebFetch.
  Rejected: porting the deep-research repo's endpoint/embeddings stack —
  external infra and keys against marginal quality gain.
- **Research reports are first-class artifacts** at
  `.shipd/research/<slug>/report.md`, installed and read through engine verbs
  (the spec-io rule holds: skills never construct storage paths). They ride
  the normal content-dir convention and travel in PRs.
- **The last human gate is epic approval.** After `epic-set-status ready`,
  no human interaction is required on the happy path. The per-member gate
  is *automated*: a context-sufficiency check of the emitted plan against
  the codebase.
- **New lifecycle status `rejected`.** None of
  `draft/ready/active/complete/verified` means "bounced for insufficient
  context", so the vocabulary gains `rejected`: entered by the context gate
  (from `draft`), exited by human enrichment (back to `draft`/`ready`),
  guarded like every transition. Rejected members pause only themselves —
  the autopilot continues with the remaining members and reports the parked
  ones.
- **The pipeline is config-defined.** An `autonomous-pipeline` key in the
  layered `.shipd-config.json` declares the stage list against a registry of
  named stages (research, epic, plan, gate, build, review). Stages can be
  **skipped**, **replaced** by a custom implementation, or **inserted**
  between existing ones. Per the layering rule the key merges
  nearest-wins-wholesale: a repo's pipeline definition replaces the
  workspace's entirely — no deep-merging of step lists. Absent the key, the
  built-in default pipeline (all stages, both gates) runs.
- **Stage contract: artifact-in/artifact-out.** Every stage consumes and
  produces the on-disk artifacts of the am convention (research report,
  epic.md, plan dir, status transitions, PR). A replacement stage is legal
  iff it honors the artifact contract at its seams — a different research
  implementation must deposit a conforming `.shipd/research/<slug>/report.md`;
  downstream stages never know. This contract is what makes skip, replace,
  and insert safe.
- **Tool bindings with declared fallback.** A stage override may bind a
  tool (e.g. Sourcebot as an additional context provider for plan
  investigation or the gate). Interactively-authenticated MCP servers can
  be absent in headless runs, so every binding declares a fallback
  (degrade to built-in search) — a missing tool degrades the stage, never
  crashes the pipeline.
- **Gates are skippable only explicitly.** The default pipeline always
  includes the context-sufficiency gate and the semantic-review check. An
  explicitly authored `autonomous-pipeline` that omits a gate, or an
  explicit skip entry for it, is a legitimate configuration — external CI
  may cover the same ground. What never happens is a silent or accidental
  gate drop: no gate disappears unless the config author wrote that intent
  down.
- **Headless driving reuses the evals resume-loop pattern** (grade-gated
  resumes answering checkpoints with the session's own recommendations,
  bounded by max-resumes) proven by the eval runner — one driving idiom,
  two consumers.
- **Semantic review is repo-agnostic with graceful degradation**: AST-aware
  analysis where a language adapter exists (user-supplied sample code seeds
  the adapter design at member planning), structural-text review otherwise
  — a missing adapter degrades the review, never blocks it.
- **Rejected plans are recovered through `/s:plan`, and runs are
  observable.** Invoking `/s:plan` on a `rejected` change (wherever its
  worktree lives) switches the skill to enrichment: diagnose the in-plan
  findings, resolve what the codebase answers, interview only the true
  gaps, then re-gate. Autopilot runs write a live heartbeat consumed by a
  board (TUI) showing runs scoped by epic, each spec's stage, and
  initiative/theme context — a parked member is never invisible again.
- **Review verdict is a required status check.** Auto-merge proceeds only
  on ci + semantic-review green; the review posts a summary plus inline
  comments on the PR, CodeRabbit-style, via `gh`.

## Design

The pipeline, end to end (the default stage list; an `autonomous-pipeline`
config key may skip, replace, or extend any of it per the stage contract):

```
/s:research <question>          →  .shipd/research/<slug>/report.md (cited)
/s:epic (research-fed)          →  .shipd/epics/<slug>/epic.md   [HUMAN: approve]
autopilot, per member (sequential, risk-ordered from the stub table):
  headless /s:plan              →  member plan in its worktree
  context-sufficiency gate       →  ready → build   |   rejected → park
  headless /s:build             →  auto-merging PR
  PR gates                       →  ci  +  semantic review (required checks)
rejected members                 →  reported for human enrichment → re-enter
```

Configuration resolves through the existing layered `.shipd-config.json`
machinery: the autopilot reads the effective `autonomous-pipeline` value
(workspace default, repo override, nearest wins wholesale), validates it
against the stage registry, and drives whatever stage list survives —
binding stage tools where declared and applying their fallbacks when a
tool is unreachable.

Pieces and seams: the research skill is freestanding (member 1); epic
authoring gains a report-consuming door (member 2); the gate and the
`rejected` status extend the status engine (member 3); the stage registry
and config schema are their own piece (member 4); the autopilot driver
composes existing skills headlessly over that registry (member 5); the
semantic engine is a standalone analyzer (member 6) that the PR gate wires
into GitHub checks (member 7); plan enrichment gives rejected plans an
interactive recovery flow through `/s:plan` (member 8); the delivery
dashboard instruments autopilot runs and aggregates the whole board
(member 9). Members 1–4 are mutually independent; 5 depends on 3 and 4;
7 depends on 6; 8 depends on 3; 9 depends on 5; the pipeline is fully
assembled when 5 and 7 land, and fully operable when 8 and 9 land.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| deep-research-skill | /s:research staged pipeline over built-in web tools emitting a cited report artifact | medium | low | medium | low |
| research-fed-epics | /s:epic consumes a research report as pre-investigation context with cited Decisions/Design | low | medium | low | low |
| context-sufficiency-gate | Automated plan-vs-codebase context check plus the new guarded `rejected` status | medium | high | high | medium |
| pipeline-config | `autonomous-pipeline` config schema, stage registry, skip/replace/insert semantics, tool bindings with fallbacks | medium | medium | medium | low |
| epic-autopilot | Headless driver: plan → gate → build → PR per member over the configured stage list, parked-member reporting | high | high | high | high |
| plan-enrichment | `/s:plan` rejected-mode recovery: locate verb, gap diagnosis from the in-plan report, enrichment interview, re-gate | medium | medium | low | low |
| semantic-review-engine | AST-aware semantic diff analyzer with language adapters and structural-text fallback | high | medium | high | medium |
| semantic-review-gate | CodeRabbit-style PR summary + inline comments and a required status check wired to auto-merge | medium | high | medium | medium |
| delivery-dashboard | Autopilot run heartbeat, board aggregator verb, curses TUI: runs by epic, spec stages, initiative and theme context | high | medium | medium | medium |
