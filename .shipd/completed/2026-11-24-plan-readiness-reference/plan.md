# plan-readiness-reference
Status: verified

## Idea

Hold the plan readiness rules once, in an engine-neutral reference, so the Claude engine and an external harness load the same text.

### Motivation

An external harness that cannot run commands or print terminal text cannot load `readiness.md`, which mixes the readiness rules with interactive steps. Its plans therefore drift from the readiness bar the Claude engine applies.

### Details

- Add `plugins/s/skills/plan/references/readiness-rules.md` with eight `##` parts: Problem and motivation, Scope and non-goals, Affected capabilities and files, No open task-shaping decision, The gate, Attestation, Self-review, Stop when ready. It is prose only.
- Replace the moved text in `readiness.md`, `plan/SKILL.md`, and `emission.md` with pointers. The print block, the question ladder, and the depth-path material stay in `readiness.md`.
- Word the runnable-premise rule for an engine that cannot run commands: cite the implementing lines, state the premise is unrun, and make the first dependent task run it.
- Fix `emission.md`'s Requirements pointer to say an id unique within the change.
- List the file and its headings in `plugins/s/external-loaders.json` and test the listing and the prose-only rule. Bump the plugin version.

Affected capabilities: `shipd-plan` (extended and modified) and `external-loaders` (modified).

### Non-goals

- No change to the lint, the gate, the four items, or any plan grammar.
- No change to `/s:plan`'s own runnable-premise requirement, which can run commands.
- No change to `plugins/s/harness/` bodies or references, and no paid eval run.

## Implementation

- **Move, not rewrite.** The eight parts restate the text `readiness.md` and `plan/SKILL.md` carried, as prose. The one new wording is the branch for an engine that cannot run commands.
- **Left in `readiness.md`.** The terminal print block, the read, memory, oracle, user ladder, and the depth-path material stay, because they are interactive.
- **Left in `emission.md`.** The attestation worked example keeps its code fence, and the note that the linter does not check the attestation stays.
- **Manifest and test.** The manifest gains one entry. Tests pin its headings and that the file has no code fence and no plugin-root variable.

Risk: a loader that reads a heading by other text. The manifest test guards this repo's side only.

## Readiness attestation

### Problem and motivation

The readiness rules sit in a file that mixes them with interactive steps.

Evidence:

- `plugins/s/skills/plan/references/readiness.md` carries the four items beside the terminal print block and the question ladder.

### Scope and non-goals

Only the plan references, the plan skill, the manifest, and their tests change.

Evidence:

- In scope: `plan/references/readiness-rules.md`, `readiness.md`, `emission.md`, `plan/SKILL.md`, `external-loaders.json`, `test_external_loaders.py`, the plugin version.
- Out of scope: lint, gate, harness bodies, evals.

### Affected capabilities and files

`shipd-plan` gains one requirement and modifies one, and `external-loaders` modifies its manifest requirement.

Evidence:

- Base hash from `spec_status.py base-hash external-loaders external-loader-manifest`: 8c0fd1653c93.
- Base hash from `spec_status.py base-hash shipd-plan premise-evidence-in-attestation`: 53f66fe30c85.

### No open task-shaping decision

The request fixes the headings, the source text, and what stays.

Evidence:

- Which text moves, and the wording for an engine that cannot run commands, come from the request.
