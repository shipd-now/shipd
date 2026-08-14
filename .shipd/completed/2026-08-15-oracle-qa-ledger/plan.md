# oracle-qa-ledger
Status: verified

## Idea

Record every ask-mikk oracle consultation as a referenceable `Q<n>` entry in a
`## Questions and answers` section of the emitted `plan.md`, report each settled
decision as a one-line question/answer pair, and let `/s:teach <change> Q<n>`
replay an entry so the user can correct the oracle's standing position.

### Motivation

Oracle-settled decisions are folded into the plan as ephemeral status prose, so
after the session there is no durable record of what was asked or answered and
no way to reference a settled decision. That blocks the correction loop: the
user cannot point at a specific consultation and teach the oracle a different
standing answer.

### Details

- Emit an optional `## Questions and answers` section in `plan.md` recording
  every oracle consultation in full — `ANSWER` entries with the oracle's
  position and citations, `INSUFFICIENT` entries with the user's typed
  resolution and the queued wiki-queue slug.
- Report each settled decision in user-visible text as a `Q<n>` reference with
  a one-line question summary and a one-line answer summary.
- Add an error-level lint rule validating the section's grammar when present.
- Add a `/s:teach <change> Q<n>` reference mode that prints the entry and
  ingests the user's correction into the workspace wiki.
- Extend `cat change` to fall back to `completed/*-<slug>/` so references
  survive the merge/archive.

Affected capabilities: `shipd-plan`, `shipd-spec-format`, `shipd-spec-lint`,
`shipd-teach`, `spec-io` (all modified). Impact:
`plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/plan/references/emission.md`,
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/skills/teach/SKILL.md`,
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/scripts/spec_status.py`, `.shipd/README.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump); no new dependencies.

### Non-goals

- The autopilot's direct oracle consult (epic-member preflight questions) keeps
  its current unrecorded reporting; only plan-flow consultations are ledgered.
- No change to the oracle agent's verdict contract or its queue write path.
- No new engine verb for reading a single ledger entry — teach reads the entry
  out of the `cat change` output.

## Implementation

- **The ledger is a `plan.md` section, not a separate artifact.** The emit
  engine's recognized change set is `plan.md`, `specs/`, `tasks.md`, and
  `cat change` prints exactly those files, so a section rides every existing
  read/merge/archive path for free. Rejected: a `questions.md` sibling file —
  invisible to `cat change` and refused by the staged emit without engine
  changes.
- **Section grammar.** After the required sections, an optional
  `## Questions and answers` section holds one entry per oracle consultation,
  numbered in consultation order:
  `### Q<n>: <one-line question summary>` followed by dash-list fields —
  `- **Question:**` the full compact question (decision, options,
  recommendation), `- **Verdict:**` `ANSWER` or `INSUFFICIENT`,
  `- **Answered by:**` `ORACLE` or `USER` — placed directly above the answer
  so who answered is clear at a glance — `- **Answer:**` the oracle's
  position in full (for `ANSWER`) or the user's typed resolution (for
  `INSUFFICIENT`), plus `- **Cited:**` source list on `ANSWER` entries and
  `- **Queued:**` the `q-<slug>` on `INSUFFICIENT` entries. Entries are
  paraphrased so they never contain the context gate's placeholder markers or
  the two-word open-question phrase its marker scan matches — the gate scans
  all of `plan.md` outside its own section.
- **Every consultation is recorded** (oracle-settled decision; cited
  `epic/mikk-knowledge`, `verified/shipd-teach`, `verified/shipd-plan`). An
  `INSUFFICIENT` entry carrying the user's resolution plus its `Queued:` slug
  gives `/s:teach` a drainable answer for a queue entry that would otherwise
  stay pending forever. Rejected: `ANSWER`-only ledger — recreates the
  "knowledge never compounds" failure mode the mikk-knowledge epic rejected.
- **Error-level lint, mirroring the epic `## Research` pattern**
  (oracle-settled decision; cited `verified/shipd-spec-lint`): an absent
  section produces no finding; a present section must hold at least one entry,
  headers must match `### Q<n>:` numbered sequentially from `Q1`, and every
  entry needs `**Question:**` and `**Answer:**` fields. Machine-consumed
  structure gets a lint rule, like `[req:]` tags and the plan header.
- **Reporting shape.** Each settled decision is reported as
  `Q<n> — <question summary> → <answer summary>` with who settled it and its
  citations, and the report names `/s:teach <change> Q<n>` as the correction
  path. Applies wherever oracle-settled decisions are reported: the context
  brief, pre-gate status text, and the depth path's brief/summary.
- **`cat change` completed fallback.** `cmd_cat`/`_change_dir` resolves
  `planned/<slug>` first, then globs `completed/*-<slug>`; on multiple
  archive matches the lexicographically last (newest date prefix) wins.
  Verified premise: `cat change plan-attestation-table` exits 1 today with
  "not found (…/.shipd/planned/plan-attestation-table)" even though
  `completed/2026-08-14-plan-attestation-table` exists — and
  `teach/SKILL.md` already directs `cat change` at completed changes, so this
  aligns the engine with the teach contract.
- **Teach reference mode.** An invocation argument matching
  `<change> Q<n>` short-circuits the sweep: resolve the change via
  `cat change`, print the entry verbatim, interview the user for the corrected
  standing position, then run the existing staged wiki emit — updating the
  entry's `Cited:` page when one exists (update-don't-duplicate), writing the
  correction verbatim into a dated `sources/` file, and draining the entry's
  `Queued:` queue block in the same ingest when present. An unresolvable
  change or entry reference reports and stops.
- **Risk: plan token budget.** The ledger adds prose to `plan.md`, whose
  linter warns above ~8,000 characters. Guarded by construction: compact
  questions are bounded (decision/options/recommendation), and the emission
  guidance says to trim, not restate, transcripts.

## Questions and answers

### Q1: Which consultations does the plan's ledger record?
- **Question:** Should the `## Questions and answers` section record every
  oracle consultation, or only oracle-`ANSWER` entries? Options: (1) every
  consultation — `ANSWER` entries with the oracle's position and citations,
  `INSUFFICIENT` entries with the user's typed resolution and the `Queued:`
  slug; (2) `ANSWER`-only. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Record every consultation — option 1. An `ANSWER`-only ledger
  recreates the "knowledge never compounds" failure mode the mikk-knowledge
  epic explicitly rejected: nothing carries the user's typed resolution back
  to the queue entry, which stays pending forever. Recording the resolution
  beside the `Queued:` slug gives `/s:teach` a drainable answer source
  through a surface it already scans, and keeps `Q<n>` references uniform
  across oracle-settled and user-settled decisions.
- **Cited:** epic/mikk-knowledge, verified/shipd-teach, verified/shipd-plan

### Q2: Does the linter enforce the ledger's grammar?
- **Question:** Should `spec_lint.py` validate the section — sequential
  `### Q<n>:` headers with Question/Answer fields — or is the grammar
  authoring guidance only? Options: (1) error-level lint when the section is
  present, absent section clean; (2) guidance only. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Lint it — option 1. The standing convention is that structure a
  machine consumes gets an error-level lint rule (`[req:]` tags, the plan
  header, epic sections, citation markers), and `Q<n>` headers are consumed
  mechanically by `/s:teach`. Mirror the epic `## Research` shape: an absent
  section produces no finding; a present section must conform, with errors
  naming the entry.
- **Cited:** verified/shipd-spec-lint
