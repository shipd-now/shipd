# amend-facts-only
Status: verified

## Idea

Make every epic amendment rewrite the epic to state the current facts, with no dated stamps and no superseded text, because git history already records what changed.

### Motivation

Anyone reading an amended epic must reconstruct the current rule from dated stamps and superseded paragraphs, as `review-rubric` shows with three successive surface counts in one Decision. Git already keeps that history, so the notes only cost readers.

### Details

- Replace the stamp rule in the epic skill's amend mode with a facts-only rule: rewrite, extend, or delete Decision text so every bullet reads as the present truth, and never append a dated marker or a before-and-after narrative.
- Mirror the rule in the harness epic body and reference, the knowledge capture rubric, the plan and build skills, and `AGENTS.md`.
- Update the `shipd-epic` and `spec-status` specs, the engine's amend-check comment, and its test fixtures, adding a test for an in-place rewrite.
- Strip the five stamps from `.shipd/epics/review-rubric/epic.md`, collapsing the surfaces Decision to its final fact, and restate the amendment Decision in `.shipd/epics/epic-knowledge/epic.md`.
- Bump the plugin version.

Affected capabilities: `shipd-epic` (modified), `spec-status` (modified). Impact: `plugins/s/skills/epic/SKILL.md`, `plugins/s/harness/bodies/epic.md`, `plugins/s/harness/references/epic.md`, `plugins/s/skills/epic/references/capture-rubric.md`, `plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md`, `AGENTS.md`, `plugins/s/skills/build/scripts/spec_status.py` (comment only), `plugins/s/skills/build/tests/test_spec_status.py`, two epic files, `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No engine enforcement of the facts-only grammar. The verb `epic-amend-check` keeps guarding protected sections only; a stamp is prose the reviewer catches, exactly as the stamp rule was.
- The protected-section gate, the fresh worktree, the two gates, and the PR or store-commit shipping flow are unchanged.
- The wiki's append-only `log.md` entries and the `Captured:` date on memory pages stay. They are a store's operations log, not notes written onto an amended artifact.
- No edit to any protected section of the two cleaned epics, and no edit under `.shipd/completed/`.

## Implementation

- **The rule becomes "state the fact".** Amend mode's step 4 says: write each touched Decision as the present truth. A new Decision states its rule. A superseded Decision is rewritten in place. A Decision no longer true is deleted. Nothing carries a date, an "amended" marker, or a "previously/now" narrative, because `git log -p` on the epic file is the amendment history. Rejected: keeping stamps but collapsing superseded text, since the stamp itself is the history note the request rules out.
- **"Accretes" becomes "changes".** The skill, the harness reference, and the engine comment describe a live epic as one whose Decisions and shelf may change while its settled substance may not drift. The word "accretes" implied additive-only edits and is dropped wherever it describes amendment.
- **Every mirror changes in the same PR.** The harness body and reference, the capture rubric, the plan and build skills, and `AGENTS.md` all restate the stamp today; each is rewritten so no surface teaches the old grammar. The harness body stays at or under its current 118 lines, because the `epic-authoring-rubric-consult` scenario pins a 120-line budget.
- **The engine changes only in comment and tests.** The verb never reads Decision text, so no code path changes. Test fixtures drop the stamp, and one new test rewrites one bullet in place and deletes another, expecting a clean exit 0, so the engine premise the new rule rests on is pinned. Rejected: a lint rule rejecting `*(amended` text, since a rule that cannot see intent would also reject a legitimate sentence quoting the old grammar.
- **The two completed epics are cleaned in this change, not through amend mode.** Amend mode ships one epic per PR from its own worktree; this change is the one that retires the stamp grammar, so it carries the cleanup of both files. Only `## Decisions` is touched in each, which `epic-amend-check` confirms in the worktree with exit 0 against `main`.
- **The collapsed surfaces Decision is authored in the task text**, so the executor copies rather than composes. Its content comes from the epic's own stamped paragraphs: four surfaces, judgement passes on three of them, the JSON payload on two.

Risk: a build-time skill session running the cached plugin snapshot still teaches the stamp until the version bump lands and the snapshot is refreshed; the bump task and the constitution's refresh rule cover it.

## Readiness attestation

### Problem and motivation

Every amended epic accumulates dated stamps and superseded paragraphs, so a reader must reconstruct the current rule from a narrative that git already keeps.

Evidence:

- `plugins/s/skills/epic/SKILL.md:128-138` mandates the `*(amended YYYY-MM-DD: <note>)*` stamp and forbids rewriting or deleting existing Decision text.
- `.shipd/epics/review-rubric/epic.md:47-80` holds one Decision stating two, then three, then four surfaces under two stamps.
- Requirement `epic-amend-mode` in capability `shipd-epic` binds the stamp.

### Scope and non-goals

The change rewrites the amendment discipline across the epic skill, its harness mirrors, three sibling references, two specs, the engine test fixtures, and the two stamped epics; the protected-section gate, the shipping flow, and the wiki log stay as they are.

Evidence:

- In scope: `plugins/s/skills/epic/SKILL.md:9,64,128-138`, `plugins/s/harness/bodies/epic.md:18-20`, `plugins/s/harness/references/epic.md:96-100`, `plugins/s/skills/epic/references/capture-rubric.md:36-37`, `plugins/s/skills/plan/SKILL.md:620-621`, `plugins/s/skills/build/SKILL.md:475-476`, `AGENTS.md:113-114`, `plugins/s/skills/build/scripts/spec_status.py:2463-2466`, `plugins/s/skills/build/tests/test_spec_status.py:7146-7157,7224-7234,7260-7268`, `.shipd/epics/review-rubric/epic.md:47-138`, `.shipd/epics/epic-knowledge/epic.md:63-69`.
- Out of scope: `plugins/s/skills/build/scripts/spec_status.py:2526-2542` (the findings function) is not edited; `plugins/s/skills/build/scripts/spec_lint.py` gains no rule; wiki `log.md` handling in `spec_common.py:1983` is untouched.

### Affected capabilities and files

Two capabilities and twelve files are affected: the prose surfaces that teach the stamp, the engine comment and tests that model it, the two epics that carry it, and the plugin manifest.

Evidence:

- Capability `shipd-epic`: requirements `epic-amend-mode` (base f6f126f9594a) and `knowledge-capture-rubric` (base b94eb0d5c570), hashes from `spec_status.py base-hash`.
- Capability `spec-status`: requirement `epic-amend-check-verb` (base dcf716312aa0).
- Files: the eleven listed under scope plus `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `spec_status.py --root <scratch repo> epic-amend-check demo` on a branch whose only edit rewrote one Decision bullet in place with no stamp printed `epic-amend-check: clean (no findings).` and exited 0.
- Runnable premise: `python3 -m unittest plugins.s.skills.build.tests.test_spec_status.EpicAmendCheckTest` ran 12 tests, OK.
- Runnable premise: `grep -c -i amend plugins/s/bin/shipd` printed 0, so the binary carries no amendment logic.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Whether to clean the two completed epics: settled by investigation of the request, which states such notes are never wanted.
- Whether to add engine enforcement: settled by investigation; the request asks for the discipline, and the existing reference already states no verb enforces the grammar.
- Personal memory store: absent, so no captured preference applied.
