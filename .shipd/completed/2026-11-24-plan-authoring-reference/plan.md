# plan-authoring-reference
Status: verified
Planned-at: c938fcbcfabf09ae41549d7e931f720b87f451d4
Gated-hash: ef9f7b570942

## Idea

Hold the plan-authoring rules once, in an engine-neutral reference, so the Claude engine and an external harness load the same text.

### Motivation

An external harness that renders markdown itself and has its own write tools cannot load `emission.md`, which mixes the authoring rules with Claude-engine grammar and commands. Its plans therefore drift from the rules the Claude engine follows.

### Details

- Add `plugins/s/skills/plan/references/authoring.md` with eight `##` parts: Motivation, Non-goals, Implementation decisions, Requirements, Scenarios, Tasks, Placeholders, Size. It is prose only, with no code fence, command, or `${CLAUDE_PLUGIN_ROOT}` path.
- Replace the moved prose in `emission.md` and the placeholder phrasing in `readiness.md` with pointers to those headings. Grammar, worked examples, the `base:` hash section, and the ledger section stay in `emission.md`.
- Point `plan/SKILL.md` at the new file in its path list and its emit step.
- List the file and its headings in `plugins/s/external-loaders.json` and test the listing and the prose-only rule.
- Bump the plugin version.

Affected capabilities: `shipd-plan` (extended) and `external-loaders` (modified).

### Non-goals

- No change to the lint, the gate, or any plan grammar.
- No other text leaves `plan/SKILL.md`, and the readiness checklist items stay as they are.
- No paid eval run.

## Implementation

- **Move, not rewrite.** The eight parts restate the rules `emission.md` and `readiness.md` carried, as prose. The one new wording is the Scenarios part: one concrete WHEN with an optional GIVEN and an observable THEN.
- **Left in `emission.md`.** The `[req: ...]` tag syntax and its lint rules, the `PLANNER` and `Relied on by` ledger text, the ledger's own field rules, and the runnable-premise sentence stay, because they are Claude-engine grammar or pinned by tests. Rejected: moving them too, since the reference would then carry engine syntax.
- **Placeholders keep their ledger sentence.** The ledger section keeps its note to trim to the decision, the options, and the answer. The marker list and the paraphrase rule live only in `authoring.md`.
- **Manifest and test.** The manifest gains one entry; a test pins its headings and that the file has no code fence and no plugin-root variable.

Risk: a loader that reads a heading by other text. The manifest test guards this repo's side only.

## Readiness attestation

### Problem and motivation

The authoring rules sit in files that mix them with Claude-engine mechanics.

Evidence:

- `plugins/s/skills/plan/references/emission.md` carries the Idea, ADR, EARS, and task-discipline prose beside grammar and commands.
- `readiness.md` and `emission.md` each restate the placeholder phrasing rule.

### Scope and non-goals

Only the plan references, the plan skill's path list, the manifest, and their tests change.

Evidence:

- In scope: `plan/references/authoring.md`, `emission.md`, `readiness.md`, `plan/SKILL.md`, `external-loaders.json`, `test_external_loaders.py`, the plugin version.
- Out of scope: lint, gate, evals.

### Affected capabilities and files

`shipd-plan` gains one requirement and `external-loaders` modifies its manifest requirement.

Evidence:

- Base hash from `spec_status.py base-hash external-loaders external-loader-manifest`: 6e8a1dc04e66.
- `test_epic_grill_contract.py` and `test_prompt_notation.py` read `emission.md`, so the `PLANNER`, `Relied on by`, and `base:` text stays there.

### No open task-shaping decision

The request fixes the headings, the source text, and what stays.

Evidence:

- Which sentences move, and the Scenarios wording, come from the request.
- The one judgement call is the readiness phrasing rule, which becomes a pointer because it restated the same rule.
