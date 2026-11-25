# gate-new-path-declaration
Status: verified
Theme: reliability
Planned-at: eef045d24392a67245d5da91af6af0887dfd58f4
Gated-hash: 6dcaf37898cb

## Idea

Teach the context gate to accept paths a task declares it will create, and to skip slash tokens that cannot be repository paths.

### Motivation

Planners cannot get a correct plan past the gate when its tasks create a new directory tree. They are left to add placeholder directories or remove backticks, which hides the paths from drift and overlap checks.

### Details

- A path directly after `Create` or `Add` in `tasks.md` is declared new; it and its parent directories count as existing.
- A token whose final segment has no dot is skipped when its top-level directory neither exists nor is declared.
- The finding text states the remedy.
- The plan guidance states the citation rules and forbids removing backticks to pass.

Affected capabilities: `context-gate` (three added requirements), `shipd-plan` (one modified, one added). Impact: `plugins/s/skills/build/scripts/spec_gate.py`, `plugins/s/skills/build/tests/test_spec_gate.py`, `plugins/s/skills/build/tests/test_external_loaders.py`, `plugins/s/skills/plan/references/authoring.md`, `plugins/s/skills/plan/references/enrichment.md`, `plugins/s/harness/references/plan.md`, `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `cited_paths` in `spec_common.py`, so drift and overlap checks behave as before.
- No new marker syntax in `tasks.md`.
- No edit to the `repo-foundation` plan or any existing plan.
- The repository root does not become an accepted parent or grandparent.

## Implementation

- **Declaration (Q1).** `declared_paths(text)` in `spec_gate.py` walks `BACKTICK_RE.finditer(text)`. A token is declared when the text before it matches `\b(?:create|add)\s+$`, ignoring case, so a line wrap is allowed. It must match `PATH_TOKEN_RE` after one leading `./` is stripped, must not be absolute, and must hold no `..` segment. Rejected: prose inference such as "Add a test to", because it would hide typos in edits.
- **Implied directories.** Every ancestor of a declared path counts as an existing directory for the parent and grandparent tests, anywhere in `tasks.md`, whatever the task order.
- **Skip rule.** A token is skipped when its final segment has no dot, its first segment is neither a directory under the root nor an implied directory, and it does not start with `artefacts/`. Existing checks run first, so this only removes findings. Rejected: skipping every token under a missing top-level directory, because it hides mistyped file paths.
- **Root stays excluded.** Accepting the root as a grandparent would pass every `a/b.ext` shorthand such as `dist/index.js`. The spec now says so.
- **Normalization.** One leading `./` is stripped from a token only for the declared lookup and the skip rule's first segment, and for the implied-directory lookup. The parent and grandparent of the token as written drive the on-disk tests, so `./src/index.ts` keeps passing.
- **Message.** The finding keeps "neither its parent nor grandparent directory exists" and appends: "write the full path from the repository root, or declare a new file by writing Create directly before it".
- **Spec shape.** Three added requirements refine `context-sufficiency-checks`, as `artefact-reference-resolution` already does. Rejected: modifying it, because its text quotes the placeholder markers and the gate would reject the delta.
- **Guidance.** The rules go in `authoring.md`, `## Tasks`, as prose, keeping its eight headings and no code fence. `enrichment.md` and the harness copy get the same enrichment rule.

Risk: a typo inside a declared path passes. Review must catch it; the exact adjacent verb keeps edits checked.

Risk: a mistyped extensionless path under an unknown top-level directory passes. Such tokens were mostly branches, ratios and repository names in the corpus run.

Risk: the unmerged `plan-size-warning` change edits the same script and test file. It touches different functions, so a conflict is textual.

## Questions and answers

### Q1: How does the gate recognise an intentionally new deep path?
- **Question:** Should the gate accept an explicit Create or Add before the path, accept any path under a missing top-level directory, or stay unchanged with guidance only? Recommendation: the explicit verb.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** An explicit Create or Add directly before the backticked path.
- **Queued:** q-gate-new-path-declaration

## Readiness attestation

### Problem and motivation

Planners creating new trees cannot pass the gate with correct plans.

Evidence:

- `plugins/s/skills/build/scripts/spec_gate.py:368-394` is the check.
- Requirement `context-sufficiency-checks` gives no exception for a new tree.

### Scope and non-goals

Only the gate's path check and the citation guidance change.

Evidence:

- In scope: `plugins/s/skills/build/scripts/spec_gate.py:368-394`.
- Out of scope: `plugins/s/skills/build/scripts/spec_common.py:3497-3517`.

### Affected capabilities and files

Two capabilities and seven files change.

Evidence:

- `context-gate`: adds `declared-new-paths`, `non-path-token-skip` and `task-path-remedy`.
- `shipd-plan`: `enrichment-gap-diagnosis` (base 1a9f6c2a71b6).
- Script: `plugins/s/skills/build/scripts/spec_gate.py:368-394`.
- Guidance: `plugins/s/skills/plan/references/authoring.md:45-54`, `plugins/s/skills/plan/references/enrichment.md:31-32`, `plugins/s/harness/references/plan.md:149-153`.
- Tests: `plugins/s/skills/build/tests/test_spec_gate.py:436-475`, `plugins/s/skills/build/tests/test_external_loaders.py:57-72`. Version: `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `_check_task_paths` on the `repo-foundation` tasks returned 16 findings; a scratch prototype returned none.
- Runnable premise: the prototype over 543 completed plans added no finding.
- Runnable premise: `python3 -B -m unittest tests.test_spec_gate tests.test_external_loaders` ran 69 tests, OK.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Declaration form: the user, Q1.
- Skip rule, root exclusion, spec shape, gate-only scope and guidance location: investigation. The user confirmed the shared summary; the spec shape was settled afterwards by the gate and the existing precedent.
