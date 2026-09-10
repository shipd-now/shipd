# document-skill
Status: verified

## Idea

Add a new plugin skill `/s:document` that carries the shipd documentation
standard — an STE-adapted rule set with a mermaid diagram policy and hard
length caps — plus a stdlib-only lint script enforcing the mechanically
checkable rules.

### Motivation

The `docs/` tree has grown dense (~2,900 lines across 15 files, one file at
711 lines) with no shared writing standard, and the strategic shift to
workspaces requires a large docs rework that needs a standard to rewrite
against.

### Details

- New skill directory `plugins/s/skills/document/` with `SKILL.md`,
  `references/standard.md`, `scripts/docs_lint.py`, `scripts/voice_digest.py`,
  and tests.
- The standard itself lives in `references/standard.md` — one canonical file
  other skills and AGENTS.md can reference by path — never restated in
  `SKILL.md`, which loads it and drives the authoring flow: classify the
  doc → write or rewrite to the standard → run the lint → fix findings
  until clean.
- A config-gated `SessionStart` hook injects the standard's short voice
  digest into every session, so all assistant replies — not just docs —
  follow the core rules.
- Registration: a `/s:document` row in the repo `README.md` skill table, an
  `/s:document` mention in `AGENTS.md`'s skill list plus a short rule that
  `docs/` documentation is authored and revised through `/s:document`, a CI
  `unittest discover` line for the new tests, and a plugin version bump.

Affected capabilities: `shipd-document` (new). Impact:
`plugins/s/skills/document/` (new), `plugins/s/hooks/hooks.json`,
`README.md`, `AGENTS.md`, `.github/workflows/ci.yml`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No rewrite of the existing `docs/` tree to the standard — that is the
  follow-up epic, driven through this skill once it ships.
- No workspaces-first docs restructure and no enterprise teams layout doc.
- No CI step that lints `docs/` content — the existing docs do not conform
  yet; CI runs only the lint script's own unit tests. The docs-lint CI step
  lands with the docs rewrite epic.
- No noun-cluster or STE-dictionary machine checks — noun clusters stay a
  judgment rule in `SKILL.md`; there is no controlled word list.

## Implementation

The standard, converged with the user:

- **One canonical rules file, never restated.** The whole standard lives in
  `plugins/s/skills/document/references/standard.md`, structured in three
  sections: `## Core rules` (the STE-adapted rules that apply to all shipd
  prose — docs and replies alike), `## Documentation rules` (doc-only: the
  doc-type marker, line caps, mermaid policy, glossary), and `## Voice
  digest` (a self-contained block of at most 12 lines distilling the core
  rules for conversational output). `SKILL.md` instructs reading the file by
  its `${CLAUDE_PLUGIN_ROOT}` path and never duplicates the rules — the
  same cross-skill reference pattern as the capture rubrics. Rejected:
  rules inlined in `SKILL.md` — other skills could not cite them without
  copying, and copies drift.
- **STE-adapted rules**: active voice only; descriptive sentences ≤ 25 words;
  procedural sentences ≤ 20 words; one text category (description vs
  instruction) per sentence; paragraphs ≤ 6 sentences; specific verbs (no
  vague "make"/"do"/"take" where a precise verb exists); noun clusters ≤ 3
  words. STE's controlled dictionary is replaced by a **shipd glossary**:
  each domain term (change, worktree, epic, member, workspace, initiative,
  store, wiki, oracle, gate, capability, spec) has exactly one meaning,
  defined in `SKILL.md`, used consistently. Rejected: full ASD-STE100 with
  its dictionary — it forbids necessary software vocabulary.
- **Mermaid policy — the structural test**: a diagram is allowed only when it
  carries structure prose cannot (three or more interacting components, a
  lifecycle with branches, or a topology); at most one diagram per doc; a
  diagram never restates an adjacent list or table. Mermaid fences stay as
  mermaid source in `docs/` (GitHub renders them natively) — no `shipd
  render` substitution, which is an `/s:explain` response-text concern.
- **Doc types and caps**: every doc under the standard opens with a first-line
  HTML comment marker `<!-- doc-type: concept|how-to|reference -->`; caps are
  concept ≤ 100, how-to ≤ 150, reference ≤ 250 total file lines. Over-cap
  docs are split or cut, never excused. Rejected: YAML frontmatter — GitHub
  renders it as a visible table above the doc; the comment is invisible.
- **Lint mechanics** (`docs_lint.py`, stdlib-only per the constitution):
  prose is analyzed outside code fences; headings, tables, link-reference
  definitions, and the marker line are skipped. Sentences split on `.`/`!`/`?`
  boundaries; words are whitespace tokens. **Procedural sentences are, by
  convention, the sentences inside numbered-list items** (the standard puts
  steps in numbered lists) and get the 20-word cap; all other prose sentences
  get 25. Errors: missing/unknown doc-type marker, file over its type's line
  cap, a sentence over its word cap, a paragraph (contiguous prose block)
  over 6 sentences, more than one mermaid fence. Warning only (never affects
  exit code): a passive-voice heuristic — a form of "be" followed within two
  words by a word ending in "-ed" or a common irregular participle — because
  detection is noisy. Findings print as `file:line: error|warning: message`;
  exit 0 when no errors, 1 when any error, 2 on usage/IO problems. Rejected:
  machine-checking noun clusters — reliable detection needs part-of-speech
  tagging, which stdlib cannot do honestly.
- **Skill flow in `SKILL.md`**: (1) identify the target doc(s) and classify
  each as concept/how-to/reference; (2) write or rewrite to the standard,
  glossary terms used consistently; (3) run
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/docs_lint.py"
  <files>`; (4) fix findings and re-run until exit 0; judgment rules (noun
  clusters, one-word-one-meaning, diagram justification) are self-reviewed
  against a short checklist. The skill edits docs only — it never commits,
  pushes, or opens PRs; shipping stays with the invoking workflow.
- **Voice hook — auto-apply to all replies**: `plugins/s/hooks/hooks.json`
  gains a `SessionStart` entry running
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py"`.
  The script (stdlib-only) resolves the layered configuration's `voice` key
  (same upward search as the rest of the engine; default **true**), and when
  enabled prints the `## Voice digest` section body of `standard.md` to
  stdout — which Claude Code injects into session context — then exits 0.
  When `voice` is false, or `standard.md` is missing/unparsable, or config
  resolution fails, it prints nothing and still exits 0: the hook is
  fail-soft and must never break session start. This is steering, not
  enforcement — no hook can rewrite model output; mechanical checking exists
  only for files via the lint. Rejected: `UserPromptSubmit` injection —
  fires on every message, paying the digest's tokens repeatedly for no
  added effect.
- **Registration follows house style**: `SKILL.md` frontmatter mirrors
  existing skills (name + trigger-phrase description); skills are
  auto-discovered from the directory, so registration is the README table
  row, the AGENTS.md wiring, and the version bump `0.6.201 → 0.6.202`.

Risk: the sentence splitter misfires on abbreviations and inline code
(`e.g.`, `spec_status.py`) producing false over-cap errors; guard by treating
inline-code spans as single tokens and by not splitting after a short list of
known abbreviations (`e.g.`, `i.e.`, `etc.`, `vs.`).
