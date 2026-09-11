# docs-feature-guides
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Rewrite the four feature guides — `docs/oracle.md`, `docs/prd.md`,
`docs/guardrails.md`, `docs/supersession-gate.md` — to the shipd
documentation standard through `/s:document`, splitting `prd.md` into a
concept hub plus a new `docs/prd-reference.md`.

### Motivation

None of the four feature guides carries a doc-type marker or passes
`docs_lint.py`, and `prd.md`'s 336 lines exceed every line cap. The approved
`docs-rewrite` epic assigns this member their rewrite under the marker-scoped
CI gate the `docs-lint-gate` member already installed.

### Details

- `docs/prd.md` becomes a concept hub (≤100 lines); a new
  `docs/prd-reference.md` (reference, ≤250) takes the header keys, statuses,
  template tier lists, and CLI surfaces.
- `docs/oracle.md` and `docs/guardrails.md` are each classified reference and
  trimmed in place to ≤250 lines — no split.
- `docs/supersession-gate.md` is classified concept (≤100 lines).
- Delta specs modify `oracle-user-docs` (shipd-ask), `prd-user-docs`
  (shipd-prd), `guardrails-key-docs` (shipd-config), and add a doc-pinning
  requirement to `build-context-gate`.

Affected capabilities: `shipd-ask`, `shipd-prd`, `shipd-config` (modified),
`build-context-gate` (modified — one added requirement). Impact: the four
docs plus one new doc; no engine, plugin, or CI changes.

### Non-goals

- No changes to the standard, the lint, the `/s:document` skill, or the CI
  step — fixed inputs per the epic.
- No changes to `docs/copilot-review.md` (the `docs-copilot-review-split`
  member) and no full-scope gate flip (the `docs-full-enforcement` member).
- No behavior changes — behavioral claims survive the restructuring or drop
  as duplicates; corrections only against observed command output.
- No `README.md` or `AGENTS.md` edits — no file outside the cluster links to
  any of the four docs (verified by grep).

## Implementation

**Target classifications (binding):**

| file | type | cap |
| --- | --- | --- |
| `docs/prd.md` | concept (hub) | 100 |
| `docs/prd-reference.md` (new) | reference | 250 |
| `docs/oracle.md` | reference | 250 |
| `docs/guardrails.md` | reference | 250 |
| `docs/supersession-gate.md` | concept | 100 |

**The `/s:document` flow governs every rewrite.** Read
`plugins/s/skills/document/references/standard.md` first; put the marker on
line 1; run `python3 plugins/s/skills/document/scripts/docs_lint.py <file>`
after each rewrite and fix findings until it exits 0. Observed: the lint
enforces the marker, per-type line caps, sentence caps, and passive-voice
warnings (it exits 1 today over all four files).

**Content moves, it is not re-derived.** `prd-reference.md` receives from
today's `prd.md`: the header format and recognized keys, the three-status
vocabulary with the staged re-install approval and `shipd lint --prd`, the
template tiers with their exact section lists, additive nesting, and
floor-not-ceiling rule, the `shipd search` example block, the `shipd prd`
report and roster examples with the `cited-by` semantics, `shipd render`
composition, and the epic `PRD:` header link with its linter resolution rule.
The FAQ dissolves: each fact merges into the section owning it or drops as a
duplicate. `prd.md` keeps the concept: the discover phase, the
Initiative → PRD → Epic → Change hierarchy with its mermaid diagram and the
upward-reference direction, workspace storage with chain resolution, the
no-workspace refusal, the standalone nature, a lifecycle and tier overview,
`/s:prd` as the authoring path in brief, and links to `prd-reference.md` and
`workspaces.md`.

**oracle.md keeps every pinned obligation** while reaching 250 lines: the
mermaid ladder fence, the `ANSWER` example with `Cited:` and `Evidence:`
lines, the advisory example with its `Authority: advisory` line, the
`INSUFFICIENT` example, the definitive-evidence bar, the three capture tiers
with `wiki-queue-answer`/`wiki-queue-discard`, and `/s:teach` as the
correction path. Compression comes from the sentence caps, not from cutting
obligations.

**guardrails.md keeps every pinned obligation**: both hook events over added
lines, the rule file format with the worked example, the three sources and
their precedence with the built-ins table, add/edit/override including the
same-named built-in override, cooldown behavior, both config kill-switches
with the superseded `rules` member note and `SHIPD_GUARDRAILS=off`, and the
token-cost properties with the deny-for-certain / remind-for-fuzzy guidance.

**supersession-gate.md stays one concept page**: what the gate is, build's
Phase-0 sequence (sync, `check-base`, the clean/drift/superseded outcomes),
the three finding kinds with their meanings, the exit codes, and the self-run
invocation. That invocation keeps the engine-script path — observed:
`plugins/s/bin/shipd --help` lists no `check-base` verb, so no binary form
exists. Rejected: adding an outcome diagram — it would restate the adjacent
list.

**Diagrams.** Exactly two mermaid fences survive, one per doc: the oracle
ladder (three interacting rungs with verdict branches) and the PRD hierarchy
(a four-level topology). Both pass the structural test; no doc gains one.

**Links.** No file outside the cluster links into the four docs (observed:
repo-wide grep matched nothing), so link fixes stay inside the cluster:
`prd.md` and `prd-reference.md` cross-link, and every outbound relative link
(`what-is-shipd.md`, `workspaces.md`, `copilot-review.md`, `.shipd/README.md`)
must resolve.

**Risks.** `prd.md`'s 100-line cap with an 11-line diagram is the tight
constraint; the guard is routing every format and verb detail to
`prd-reference.md` and keeping the hub at overview altitude. `oracle.md`'s
~45 lines of pinned fences leave ample room under 250.

## Questions and answers

### Q1: Split prd.md or trim it to one reference doc?
- **Question:** Should `docs/prd.md` (336 lines, over every cap) split into a
  ≤100-line concept hub plus a new `docs/prd-reference.md` (≤250), or be
  re-classified as a single reference doc trimmed to ≤250? Options:
  (a) split by type; (b) single trimmed reference. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Split by type — option (a). The epic's rule for over-cap docs
  is a split by type, its one decided instance (`copilot-review.md`) splits
  into exactly this two-doc shape, and the one-doc-one-type decision forbids
  packing the discover-phase concept into a reference doc; the wiki's
  discover-phase page cites `docs/prd.md` as backing for that concept
  content, which a trim would misfile.
- **Cited:** epic/docs-rewrite, [[discover-phase]]

### Q2: Classify oracle.md and guardrails.md as single reference docs?
- **Question:** Should `docs/oracle.md` (226 lines) and `docs/guardrails.md`
  (216 lines) each stay a single reference doc trimmed in place to ≤250, or
  split into concept-plus-reference pairs? Options: (a) single reference doc
  each; (b) split each. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Single reference doc each, trimmed in place — option (a). The
  epic reserves splitting for docs over their cap and scopes this member's
  re-classify-or-split treatment to `prd.md` alone; both files fit the
  reference cap, and stray mixed-type content is moved, not stretched.
- **Cited:** epic/docs-rewrite
