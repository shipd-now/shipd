# deep-research-skill
Status: verified
Epic: autonomous-delivery

## Idea

Feature planning starts from a blank page: nothing gathers *external* context
(prior art, APIs, published trade-offs). The autonomous-delivery epic reserved
`<content-dir>/research/` and the consuming side already landed — epics carry a
lint-validated `## Research` section and `/s:epic` reads linked reports — but
there is no producer and no report format: `research-fed-epics` explicitly
deferred both to this member.

This change supplies the producer and the format:

- A new `/s:research` skill: a staged pipeline (decompose → search → select →
  extract anchored findings → compose) over the session's built-in
  WebSearch/WebFetch tools, ending in a cited report artifact.
- Engine support: a `spec_emit.py research` install mode, a
  `spec_status.py cat research` read verb, and `spec_lint.py` report checks —
  so reports stay engine-mediated like every other artifact.
- The report grammar: a title, a numbered `## Sources` section, and inline
  `[n]` citation markers that must resolve to listed sources.

### Non-goals

- No external research infrastructure — no Tavily keys, endpoints, or
  embeddings; WebSearch/WebFetch are the whole search stack.
- No eval case for `/s:research`: the eval runner's grading is hardwired to
  plan-shaped output and a research eval needs live web access.
- No headless/autopilot contract — `research` is a pre-approval pipeline stage
  (`autopilot.py` `PRE_APPROVAL_STAGES`); the skill is human-driven.
- No library-lint walking of `research/`: reports are validated at engine
  install time and by epic-link existence checks only, preserving the
  `research-fed-epics` decision.
- No lint mandate on the report's prose sections — Summary/Findings/Gaps &
  caveats are the skill's composition guidance, not lint rules.

Affected capabilities: `shipd-research` (added), `spec-io` (modified),
`shipd-spec-format` (modified), `shipd-spec-lint` (modified), `shipd-interaction`
(modified — interactive-skill roster grows). Impact:
`plugins/s/skills/research/SKILL.md` (new),
`plugins/s/skills/build/scripts/{spec_emit.py,spec_status.py,spec_lint.py}`
and their tests, `.shipd/README.md`, `AGENTS.md`, plugin version bump.

## Implementation

- **Single-file install mode modeled on the `epic` mode.**
  `spec_emit.py research <slug> --from <file> [--replace]` copies the staged
  report to `<content-dir>/research/<slug>/report.md` via the shared
  `_install_dir` validate-then-commit helper. Rejected: a directory staging
  set — the report defines no supporting files, and a single file matches the
  epic/initiative precedent.
- **Lint mandates only the citation skeleton.** `lint_research(root, slug,
  errors)` in `spec_lint.py` checks: line 1 is a non-empty `# <title>`; a
  `## Sources` section exists with at least one numbered entry (`N. …`); every
  inline `[n]` marker resolves to a listed source number; at least one marker
  exists. Rejected: linting the section shape (Summary/Findings/Gaps) — that
  is composition guidance the skill enforces by instruction, and over-linting
  prose invites false failures.
- **Citation-marker scanning skips fenced code blocks** and ignores `[n](`
  (markdown links), so code samples with index expressions never trip the
  unresolved-marker check. This is the main false-positive risk and the guard
  is deterministic.
- **`lint_research` is not wired into `lint_library`** — the library lint
  still never walks `research/` on its own; only the emit engine calls the
  checks in-process.
- **`cat research <slug>`** joins the mediated-read verbs: parser `choices`
  gains `research`, `cmd_cat` resolves `<content-dir>/research/<slug>/
  report.md`, unknown slugs exit non-zero, and the unknown-kind error message
  lists the new kind.
- **The skill follows the interactive-skill conventions**: version
  announcement, `config-show` layout check, its own worktree
  (`worktree.sh research-<slug>`) so the report ships as one PR, a single
  batched typed clarification round only when the question is underspecified,
  and the shipd-interaction question-rejection-recovery and dialog/prose rules —
  the roster in `shipd-interaction` grows from six skills to seven.
- **Missing web tools stop the run.** If WebSearch/WebFetch are unavailable in
  the session, the skill reports that and stops — it never fabricates
  findings from model memory. Rejected: a degraded memory-only mode — an
  uncited report defeats the artifact's purpose.
- **Version bump to 0.6.0** — a new skill is a minor bump, per the 0.5.0
  autopilot precedent.

Risk: the report grammar is new and hand-authored by a model mid-session;
guarded by the emit engine's remove-on-failure install (an invalid report
never lands) and unit tests covering each lint failure mode.
