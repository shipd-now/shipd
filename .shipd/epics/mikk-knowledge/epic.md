# mikk-knowledge
Status: complete
Theme: developer-experience
Initiative: context-enhancements

## Introduction

Sessions keep hitting the same wall: a planner reaches an un-inferrable
decision, or the context-sufficiency gate rejects a plan, and the only moves
today are to interrupt the user with a question round or park the change for a
human. Worse, the answer usually *was* given once — in an earlier session, an
epic's Decisions, or a hallway-style correction — but that knowledge evaporates
between sessions and never crosses repo boundaries.

This epic adds a compounding knowledge layer to the workspace: a central
LLM-wiki store (Karpathy's llm-wiki grammar) at the workspace root, an
**ask-mikk** oracle any planning/building surface can query with one compact
question before interrupting the user, and a **teach-mikk** intake skill that
distills existing spec artifacts into wiki pages and interviews the user only
about gaps and contradictions. Unanswerable questions queue up instead of
blocking, and their eventual answers are ingested — so every escalation makes
the next one less likely.

Success criteria: a planner at a readiness gap consults ask-mikk and proceeds
without a user question round whenever the wiki holds the answer; an autopilot
member rejected by the context gate gets one oracle-backed enrichment attempt
before parking; questions the oracle cannot answer land in the pending queue
and their answers reach the wiki through teach-mikk.

### Non-goals

- No embeddings, vector search, databases, or external services — retrieval is
  index- and grep-based over markdown, and engine scripts stay stdlib-only.
- No background or scheduled ingestion (nightly lint, cron consolidation) —
  every wiki operation runs on demand through a skill or an engine verb.
- No per-repo wikis or repo/workspace overlay — one central store only.
- Not a replacement for the human: ask-mikk is a middle rung, plan's question
  rounds and autopilot's parking outcomes remain the final fallback, and the
  user remains the authority the wiki merely caches.
- No multi-user concerns — page leases, cross-machine sync, and merge
  conflict handling between concurrent wiki writers are out of scope.

## Decisions

User-made in the planning session (via typed decision round):

- **Epic scope.** This ships as an epic of member changes, not one change —
  the feature spans a new store grammar, two new skills, an agent contract,
  and two caller integrations.
- **Central store at the workspace root.** The wiki lives at
  `<ws-root>/<content-dir>/wiki/` (today
  `/Users/mikkelbergmann/projects/.shipd/wiki/`), discovered through the existing
  workspace machinery (`find_workspace_root`); it is cross-repo by
  construction. Rejected: per-repo wikis plus a shared overlay (two stores to
  search, lint, and reconcile).
- **Queue + ingest fallback.** When the oracle cannot answer, it returns
  `insufficient` together with a decision-ready compact question *and* appends
  that question to a pending-questions queue in the store; the caller falls
  back to today's behavior (typed round in plan, park in autopilot). Answers
  supplied later are ingested into wiki pages. Rejected: live interruption
  (impossible unattended) and insufficient-only (knowledge never compounds).
- **Interview + auto-ingest intake.** teach-mikk auto-distills existing
  artifacts (epic Decisions/Design, completed changes, research reports,
  project `context.md`) into wiki pages and interviews the user only about
  gaps and contradictions the scan surfaces. Rejected: interview-only (starts
  empty) and ingest-only (never captures unwritten opinion).

Binding cross-cutting choices every member inherits:

- **Karpathy llm-wiki grammar.** The store is `sources/` (immutable inputs,
  never edited by the LLM), `wiki/` (LLM-owned interlinked pages using
  `[[wikilink]]` cross-references), `index.md` (every page with a one-line
  summary, updated on every ingest), `log.md` (append-only, dated entries),
  `schema.md` (naming conventions and page grammar), and `queue.md` (pending
  questions with answer slots). Operations are exactly ingest / query / lint.
- **Lint-gated like every other artifact.** The wiki gets a `spec_lint.py
  --wiki` mode (dead wikilinks, pages missing from the index, malformed queue
  or log entries) and engine-mediated reads via `spec_status.py` verbs; no
  skill writes into the store except through the same staged, validated
  conventions the rest of the content tree uses.
- **The compact-question contract.** Every question put to ask-mikk — and
  every question ask-mikk queues for the user — is a single decision-ready
  unit: the decision, the concrete options, and the asker's recommendation.
  Never a raw trace or an open-ended essay prompt.
- **The escalation ladder is read → ask-mikk → human.** Callers consult the
  oracle only for decisions the repo cannot answer (the codebase-first rule is
  unchanged), and the oracle never blocks: in unattended runs an
  `insufficient` verdict preserves today's parking semantics exactly, plus a
  queued question.
- **Oracle answers are cited and opinionated.** ask-mikk answers from wiki
  pages and per-repo spec surfaces (capability masters, epic
  Decisions/Design, research reports, project `context.md` — all via
  `spec_status.py cat` / engine reads), names the page or artifact behind the
  answer, and takes a position rather than listing alternatives.
- **Engine constraints hold.** New scripts are stdlib-only with `--root`
  defaulting to cwd and unit tests under the owning skill; every member
  touching `plugins/s/` bumps the plugin version in its own PR.

## Design

Four pieces, joined at three seams:

```
callers                         oracle (read path)              store (workspace root)
/s:plan readiness gap ──┐                                      <ws-root>/.shipd/wiki/
autopilot gate rejection ┼─▶ compact question ─▶ ask-mikk agent   ├ sources/   (immutable)
build sub-agent QUESTION ┘                        │ search wiki   ├ wiki/      ([[linked]] pages)
                                                  │ + cat specs   ├ index.md   ├ log.md
                                                  ├ answer+cite ─▶ caller proceeds
                                                  └ insufficient ─▶ queue.md + fallback

teach-mikk (write path): scan repo ─▶ distill artifacts ─▶ interview gaps ─▶ ingest
                         (also drains queue.md answers)      pages + index + log
```

- **The store** is pure data plus engine support: directory grammar, schema,
  lint mode, and read verbs. It has no model-driven behavior of its own,
  which is why it ships first — both skills and both integrations depend on
  it and nothing else.
- **The read path** is the ask-mikk skill plus an oracle agent definition in
  `plugins/s/agents/` (spawned via the Agent tool, like `s:sub-agent` /
  `s:validator`). Input: one compact question plus the asking repo's root.
  It resolves the workspace, searches `index.md` → pages, widens to the
  asking repo's spec surfaces, and returns either an opinionated cited answer
  or `insufficient` + the queued question. It is non-interactive by contract.
- **The write path** is the teach-mikk skill: distillation of existing
  artifacts into entity/convention pages, a gap-and-contradiction interview
  (batched, options-first, matching the plugin's question discipline), and
  the ingest bookkeeping (5–15 page touch-ups, index and log updates,
  queue-draining).
- **The seams the decomposition follows:** the plan skill's readiness gap
  (prose change in `plan/SKILL.md` + readiness reference: consult ask-mikk
  between "read the repo" and "ask the user"); the autopilot's gate-rejection
  branch in `autopilot.py` (an enrichment attempt driven by the oracle before
  the `rejected` park, and oracle-aware handling where `GOAHEAD_REPLY` and
  sub-agent `QUESTION:` escalations surface); and the store's engine verbs,
  which is the only interface either caller uses — no caller touches wiki
  files directly.

Member order is dependency order: `mikk-wiki-store` → `ask-mikk-oracle` →
`teach-mikk-intake` → `plan-ask-mikk` → `autopilot-ask-mikk`. The two
integrations are independent of each other and only need the oracle.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| mikk-wiki-store | Workspace wiki store: Karpathy-grammar layout (`sources/`, `wiki/`, `index.md`, `log.md`, `schema.md`, `queue.md`), `spec_lint --wiki` mode, and engine read verbs | medium | medium | medium | medium |
| ask-mikk-oracle | ask-mikk skill + oracle agent definition: compact-question query over the wiki and the asking repo's spec surfaces, returning a cited opinionated answer or insufficient + queued question | medium | medium | medium | medium |
| teach-mikk-intake | teach-mikk skill: auto-distill spec artifacts into wiki pages, interview the user on gaps/contradictions, drain answered queue entries, full ingest bookkeeping | medium | medium | high | medium |
| plan-ask-mikk | /s:plan consults ask-mikk at the readiness gap before opening a user question round; unanswered gaps still go to the user | low | medium | low | medium |
| autopilot-ask-mikk | Autopilot tries an oracle-backed enrichment on context-gate rejection before parking, and routes driven-session escalations through ask-mikk | medium | high | medium | medium |
