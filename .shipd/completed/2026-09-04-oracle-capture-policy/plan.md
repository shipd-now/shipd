# oracle-capture-policy
Status: verified

## Idea

Give the oracle's capture path a durability policy: classify every user-typed
answer before it becomes standing oracle knowledge — capture the durable,
discard the ephemeral, and record consent-gated categories only on the user's
express instruction, as advisory rather than binding knowledge.

### Motivation

Today `/s:ask`, `/s:plan`, and the harness ask body write every typed
resolution into the wiki queue via `wiki-queue-answer` unconditionally, so a
one-off or self-evidencing answer becomes citable oracle knowledge exactly
like a durable data-pattern preference. The user wants the oracle to
auto-learn only what is deemed useful, with workaround/annoyance-type
instructions recorded solely on express request and later surfaced as
overridable recommendations, never silently binding.

### Details

- A three-tier capture rubric (include / exclude / consent-gated) as a shared
  reference file, calibrated by ten worked examples the user classified.
- A `wiki-queue-discard` engine verb so excluded answers remove their pending
  queue block instead of accumulating forever.
- An advisory capture tier (`wiki-queue-answer --advisory`) whose knowledge
  the oracle relays with an `Authority: advisory` line; callers surface it as
  the recommended default in the user round instead of folding it in.
- The teach drain preserves the advisory marking when distilling queue
  answers into wiki pages.

Affected capabilities: `shipd-wiki`, `shipd-ask`, `shipd-plan`, `shipd-teach`
(all modified). Impact: `plugins/s/skills/build/scripts/spec_status.py` and
its tests, `plugins/s/agents/oracle.md`, `plugins/s/skills/ask/SKILL.md`,
`plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/teach/SKILL.md`,
`plugins/s/harness/bodies/ask.md`, `plugins/s/harness/references/ask.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to the personal memory store or `/s:remember`/`/s:memory`
  surfaces — the rubric may recommend routing a personal preference there in
  prose, but no `shipd-memory` behavior changes.
- No embeddings or search service; oracle retrieval stays index- and
  grep-based over markdown.
- No retroactive reclassification of already-captured queue answers or
  existing wiki pages, and no autopilot/pipeline changes.

## Implementation

- **Rubric as one shared reference** at
  `plugins/s/skills/ask/references/capture-rubric.md`, staged verbatim as
  `artefacts/capture-rubric.md` and installed by a copy task; `/s:ask`,
  `/s:plan`, and the harness ask body all point at it. Rejected: restating
  the rubric in each skill — three copies drift.
- **Excluded answers discard the queue block** via a new
  `wiki-queue-discard <slug> --reason "<text>"` verb modeled on
  `cmd_wiki_queue_answer` (`spec_status.py:2907`): same store resolution,
  bare-slug input, refusal of answered blocks (those belong to the teach
  drain), auto-commit. Rejected: an ephemeral-tagged answer the teach drain
  drops — conflicts with `teach-queue-drain` as written and is citable until
  drained; leaving blocks pending — the queue accumulates dead questions.
- **Advisory marking rides the free-form `Answer:` value** as an
  `advisory: ` prefix written by `wiki-queue-answer --advisory`. The queue
  block grammar validates field presence, not answer content, so no lint or
  grammar change is needed. Drained pages carry an `Authority: advisory`
  line; the oracle emits `Authority: advisory` on an `ANSWER` whose source
  carries either marker. Rejected: a new `- Authority:` queue field — it
  would touch the store lint for no added expressiveness.
- **Advisory recall recommends, never settles.** Callers branch: a binding
  `ANSWER` folds in silently as today; an `ANSWER` carrying
  `Authority: advisory` still opens the user round with the oracle's
  position as the recommended-first option, cited — the user chooses.
- **Consent gate is express-only.** A consent-gated answer is captured
  (always with `--advisory`) only when the user expressly affirms a
  record-this question; anything else discards. Capture and discard failures
  are reported and never block the flow, preserving the existing contract.
- Verified premises: `wiki-queue-add`/`wiki-queue-answer` runs in a scratch
  workspace printed `q-test-entry` with exit 0, and re-answering an answered
  block was refused with exit 1 — the discard verb's refusal semantics mirror
  that observed behavior.
- Version bump `plugins/s/.claude-plugin/plugin.json` to `0.6.175` (cache
  snapshot is version-keyed).
- Risk: existing wikis hold no advisory content, so the oracle change is
  backward-compatible — absent markers mean binding, today's behavior.

## Questions and answers

### Q1: Record a clean framework/package choice?
- **Question:** Should a captured answer choosing between packages (Zod vs
  Valibot) be synthesized into the oracle? Options: include | exclude |
  decide in context. Recommendation: exclude as self-evidencing.
- **Answered by:** USER
- **Answer:** Include — when it is a clean choice between different packages,
  the preference itself is durable knowledge.

### Q2: Record a data-modeling pattern?
- **Question:** Soft-delete-plus-audit-log over hard deletes — include,
  exclude, or decide in context? Recommendation: include.
- **Answered by:** USER
- **Answer:** Include — a durable cross-cutting engineering position.

### Q3: Record a workflow workaround stated in annoyance?
- **Question:** "Stop asking, just always run the PR unlock" — include,
  exclude, or decide in context? Recommendation: decide in context,
  recording only on express instruction.
- **Answered by:** USER
- **Answer:** Decide as it comes up — consent-gated; record only when
  expressly told to.

### Q4: Record a naming convention?
- **Question:** "Async accessors are `fetch*`, never `get*`" — include,
  exclude, or decide in context? Recommendation: include.
- **Answered by:** USER
- **Answer:** Include — conventions for future code are durable.

### Q5: Record an explicit one-off decision?
- **Question:** "Ship this migration without rollback, just this once" —
  include, exclude, or decide in context? Recommendation: exclude.
- **Answered by:** USER
- **Answer:** Exclude — change-scoped; the plan ledger records it, the
  oracle must not generalize it.

### Q6: Record an error-handling philosophy?
- **Question:** "Fail fast with typed exceptions, no Result wrappers" —
  include, exclude, or decide in context? Recommendation: include.
- **Answered by:** USER
- **Answer:** Include — durable architectural stance.

### Q7: Record a testing-depth preference?
- **Question:** "Prefer integration tests against the real engine over
  mocks" — include, exclude, or decide in context? Recommendation: include.
- **Answered by:** USER
- **Answer:** Include — standing test-strategy position.

### Q8: Record a tool version pin?
- **Question:** "Pin Node 22 in .nvmrc" — include, exclude, or decide in
  context? Recommendation: exclude as self-evidencing configuration.
- **Answered by:** USER
- **Answer:** Exclude — the repo file is the durable record; a copy goes
  stale.

### Q9: Record PR/process etiquette?
- **Question:** "Always squash-merge with imperative one-line subjects",
  partially enforced by repo settings — include, exclude, or decide in
  context? Recommendation: decide in context.
- **Answered by:** USER
- **Answer:** Decide as it comes up — consent-gated; tooling-enforced parts
  are already recorded elsewhere.

### Q10: Record a personal output/presentation preference?
- **Question:** "Digests use ASCII diagrams, never mermaid" — include in
  the workspace wiki, exclude, or decide in context (personal store also
  exists)? Recommendation: exclude toward the personal store.
- **Answered by:** USER
- **Answer:** Decide as it comes up — consent-gated, with the personal
  memory store as the likelier destination.

### Q11: What happens to an excluded answer's queue block?
- **Question:** Discard via a new engine verb, write a tagged answer the
  teach drain drops, or leave pending? Recommendation: discard via a new
  verb.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Discard via a new `wiki-queue-discard` verb — the queue stays
  a pending-only worklist and ephemeral answers never become citable. The
  oracle found no spec surface with a position and noted a tagged answer
  would conflict with `teach-queue-drain`.
- **Queued:** none (no discoverable workspace at the planning root)
