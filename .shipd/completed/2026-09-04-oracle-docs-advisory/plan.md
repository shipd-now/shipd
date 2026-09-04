# oracle-docs-advisory
Status: verified

## Idea

Catch the user-facing oracle guide up to the v0.6.175 capture policy:
advisory answers, the three-tier capture classification, and the
`wiki-queue-discard` verb.

### Motivation

The `oracle-capture-policy` change shipped advisory knowledge
(`Authority: advisory` answers relayed as overridable recommendations) and
classified capture (include / exclude / consent-gated, with excluded answers
discarded via `wiki-queue-discard`), but `docs/oracle.md` — the user-facing
guide the `oracle-user-docs` requirement governs — still documents
unconditional capture and only the plain two-verdict contract, so the guide
now contradicts the shipped behavior.

### Details

- Extend `docs/oracle.md`: an advisory `ANSWER` example and its
  recommended-not-forced semantics, the classified capture loop (three tiers
  per the shipped rubric, express-consent rule, discard of excluded
  answers), and a corrected capture-loop narrative and mermaid diagram.
- Extend the `shipd-ask` capability's `oracle-user-docs` requirement to
  require that content, so the guide cannot silently regress.

Affected capabilities: `shipd-ask` (modified). Impact: `docs/oracle.md`
only; no `plugins/s/` file changes, so no plugin version bump.

### Non-goals

- No behavior changes anywhere — engine, agent, and skill contracts are
  already shipped and stay untouched.
- No other docs: `docs/cheatsheet.md`'s oracle line is generic and remains
  accurate; no page besides `docs/oracle.md` describes capture mechanics.
- No restructuring of the guide beyond what the new content requires.

## Implementation

- **Source of truth for the added prose** is the merged contract: the
  `shipd-ask` requirements `oracle-cited-answers` (the
  `Authority: advisory` line and its no-line-means-binding default) and
  `ask-skill` (classification, express consent, discard), the `shipd-wiki`
  requirements `wiki-queue-answer-verb` (`--advisory` prefix) and
  `wiki-queue-discard-verb`, and the rubric at
  `plugins/s/skills/ask/references/capture-rubric.md`. The doc paraphrases
  these; it invents no new semantics.
- **Advisory coverage lands inside the existing "two verdicts" frame**: the
  first line stays `ANSWER` or `INSUFFICIENT`, and advisory is presented as
  a marked variant of `ANSWER` (an `Authority: advisory` line after the
  position) rather than a third verdict — matching the contract, where
  callers branch on the first line and then check for the authority line.
  Rejected: a "three verdicts" framing — it would contradict the
  machine-branchable first-line contract the doc already teaches.
- **The capture loop's diagram and narrative gain the classification**: the
  mermaid capture path routes through the rubric's three tiers (include →
  `wiki-queue-answer`; exclude → `wiki-queue-discard`, nothing stored;
  consent-gated → recorded as advisory only on an express "record that").
  The diagram stays one `mermaid` fence with no box-drawing characters, per
  the requirement's rendering rule.
- **The requirement is extended, not replaced**: `oracle-user-docs` keeps
  every existing mandate (ladder diagram, both verdict examples, evidence
  bar, `/s:teach` correction path) and adds the advisory example and the
  classified capture loop, so lint and the docs site contract stay stable.
- Risk: doc drift against future capture changes; mitigated by encoding the
  new content in the requirement's scenarios, so the next contract change
  trips this requirement's scenarios rather than silently passing.
