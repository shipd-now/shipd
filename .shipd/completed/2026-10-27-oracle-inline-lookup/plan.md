# oracle-inline-lookup
Status: verified
Theme: developer-experience
Planned-at: f933635fe102262364f6f9493a39e9d50c33e701
Gated-hash: 239117b987b0

## Idea

Replace the `s:oracle` subagent with one engine verb, `spec_status.py
oracle-lookup`, that every caller runs inline, cutting a consultation from
about 49K tokens to under 5K.

### Motivation

Every oracle consultation — each `/s:ask`, each `/s:plan` question round, each
unattended autopilot session — spends about 49K tokens, about 37K of it
fixed subagent overhead before a single store is read. Users asking one
quick question pay the price of a full agent spawn, and autopilot multiplies
it per gap.

### Details

- Add `oracle-lookup <term>...` to `spec_status.py`: one read-only call
  that walks personal → workspace chain (pages, answered queue) → base →
  spec surfaces and prints at most 6000 characters of cited snippets, plus
  a not-evidence list of matching pending queue blocks.
- Add `plugins/s/skills/ask/references/oracle-contract.md` (≤120 lines):
  the compact-question shape, how to run the verb, the judging rules, the
  verdict grammar, and the queue path.
- Switch `/s:ask`, `/s:plan`, the autopilot skill, `autopilot.py`'s four
  session prompts, and the harness `ask` body to inline consultation.
- Retire `plugins/s/agents/oracle.md` and `plugins/s/harness/agents/oracle.md`;
  drop `oracle` from `AGENT_ROLES`.
- Update `docs/oracle.md`, `docs/harness-agents-reference.md`,
  `docs/customise.md`, `README.md`, and the harness `ask` reference.

Affected capabilities: `spec-status` (added verb), `shipd-ask`,
`shipd-plan`, `epic-autopilot`, `harness-registry`,
`harness-command-bodies`, `harness-verb` (modified).

### Non-goals

- No change to the verdict grammar, the `## Questions and answers` ledger,
  the capture rubric, or the queue verbs.
- No cleanup of `shipd-oracle` agent files that earlier harness installs
  already wrote; they stay harmless and unused.
- No embeddings or search service — retrieval stays term-hit over markdown.

## Implementation

- **Verb placement.** Add `cmd_oracle_lookup(root, terms)` to
  `plugins/s/skills/build/scripts/spec_status.py` beside `cmd_search`, and
  register `oracle-lookup` with positional `terms` (nargs `+`) like
  `search`. Reuse `_wiki_show_data`'s resolution (personal store via
  `sc.memory_store_dir`, chain via `sc.workspace_chain`, fallback via
  `_resolve_wiki_anchor`, base via its `base` field) and `_dir_names`.
  Rejected: shelling out to `cat wiki` from the skill — that is the
  nine-call walk this change removes.
- **Matching.** Split each file into paragraphs on blank lines; a queue
  block is one unit. A unit matches on ≥2 distinct terms (or the one term
  when only one is given), case-insensitive substring like
  `_related_score`. Rank by distinct terms, then total hits. Rejected:
  whole-file ranking as in `search` — the caller needs the quotable
  sentence, not a file name.
- **Spec surfaces.** `verified/*/spec.md` cites `verified/<cap>
  (<requirement-id>)`, taken from the nearest preceding `id:` line;
  `epics/*/epic.md` only inside `## Decisions` and `## Design`;
  `research/*/report.md`. Focus project repos come first: read
  `workspace-show`'s data (`focus`, project repos with `present`), resolve
  each present repo path against the workspace root, then the invocation
  root, deduped.
- **Output format** (plain text, one snippet per line):

  ```
  oracle-lookup: terms=<t1, t2> | personal: <path|skipped> | workspace: <store|skipped> | base: <path|none|absent> | specs: <roots>
  == personal
  [[slug]] (personal) — "<snippet>"
  == workspace
  queue q-slug [advisory] — "<snippet>"
  == base
  (none)
  == specs
  verified/semantic-review (review-base-ref) — "<snippet>"
  == pending queue (duplicate check — not evidence)
  q-slug — <question>
  no evidence found — verdict INSUFFICIENT
  ```

  The last line prints only when every evidence rung is `(none)`. When the
  6000-character cap stops output, the final line reads `… <n> more
  matches omitted`.
- **Contract reference.** The caller reads `oracle-contract.md` once per
  session; it restates the judging rules that `oracle.md` held, trimmed to
  the verb-based flow. `/s:ask`, `/s:plan`, autopilot prompts, and the
  harness body point to it rather than copying it.
- **Autopilot prompts.** In `autopilot.py`, `GOAHEAD_REPLY`, the build and
  enrich stage prompts, and the replan prompt name `python3 <STATUS_PY>
  --root <repo> oracle-lookup <terms>` (the module's `STATUS_PY` constant)
  and the contract reference path under `PLUGIN_DIR`, in place of "spawn
  agent `s:oracle`".
- **Harness.** `AGENT_ROLES` becomes `("sub-agent", "validator")`; delete
  `plugins/s/harness/agents/oracle.md`. The `ask` body drops its
  `if:subagents` delegation and runs the verb on every harness.
- **Budget.** Verb output ≤ 6000 characters (~1.5K tokens) plus the
  reference (~1.3K tokens) keeps a first consultation under 5K; later
  consultations in the same session cost only the verb output.

Risk: the caller now judges its own lookup, losing the agent's isolation.
The contract guards it with the verbatim `Evidence:` rule (the quote must
appear in the lookup output) and the default-`INSUFFICIENT` bar, and the
verb prints the INSUFFICIENT line itself when nothing matched. Risk: weak
terms miss a page; the contract tells the caller to pick distinctive terms
and allows one retry with alternative terms before judging.

## Readiness attestation

### Problem and motivation

Each oracle consultation costs about 49K tokens, about 37K of it fixed
subagent overhead.

Evidence:

- Measured 2026-10-27 on one `s:oracle` run: peak context 48,408 tokens over
  10 turns; turn 1 sat at 36,865 before any tool result.
- `plugins/s/agents/oracle.md` is 18,421 bytes and declares no `tools:`
  frontmatter, so the agent loads every tool schema.

### Scope and non-goals

One new verb, one reference, four callers switched, the agent retired;
verdict grammar, ledger, and capture stay unchanged.

Evidence:

- In scope: `spec_status.py`, `autopilot.py`, `harness_registry.py`,
  `plugins/s/skills/{ask,plan,autopilot}/SKILL.md`,
  `plugins/s/harness/bodies/ask.md`, `plugins/s/harness/references/ask.md`,
  `plugins/s/skills/document/references/harness-plan-mode.md`.
- Out of scope: `spec_lint.py` and `spec_gate.py` ledger checks (`ORACLE`
  answered-by values stay valid); `tools/port.py` (its `s:oracle` is a
  rename-rule example).

### Affected capabilities and files

Seven capabilities, because the agent is named by the ask, plan, autopilot,
and harness contracts.

Evidence:

- Bases: shipd-ask ask-skill 6d566594c98c, compact-question-contract
  6bfa4ab32330, oracle-fallback-store f78054299bf2, oracle-agent-contract
  28a229f143db; shipd-plan oracle-consultation 2bc4006b4c82; epic-autopilot
  oracle-gate-enrichment 9bce2e993633, oracle-aware-driven-sessions
  4efda61971ea, detached-pre-build-drift 355e6a134a2a,
  in-session-unattended-prompts 76000f825fac; harness-registry registry-data
  81db8cd304e4, registry-agent-source a971f7cb83f1, agent-surface-docs
  87e388aac461; harness-command-bodies delegation-agent-ids a5f22df62539;
  harness-verb agent-rendering 414105e91fce — all from `base-hash`.
- Tests touched: `test_subagent_contract.py`, `test_harness_bodies.py`,
  `test_harness_generate.py`, `test_harness_registry.py`,
  `test_autopilot.py`, `test_autopilot_skill_contract.py`; new
  `test_oracle_lookup.py`.
- Runnable premise: `spec_status.py wiki-show --json` → exit 0, keys
  `store`, `present`, `fallback`, `personal`, `chain`, `base`, `pages`,
  `queue` (blocks with `id` and `fields`, including `Answer`).
- Runnable premise: `spec_status.py wiki-show --personal` with no store →
  `Error: no wiki store at ~/.shipd-memory/wiki`, non-zero.
- Runnable premise: `spec_status.py search pull request base branch` → exit
  0, ranked whole-artifact blocks — the term handling `oracle-lookup`
  mirrors.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Engine verb with no agent: chosen by the user in this session.
- Verb name, matching unit, caps, and output format: settled above from the
  existing `search` and `related` conventions.
