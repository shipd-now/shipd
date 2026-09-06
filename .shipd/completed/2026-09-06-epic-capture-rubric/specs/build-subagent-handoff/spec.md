## ADDED Requirements

### Requirement: Rubric consult in the build Q&A loop
id: build-qa-rubric-consult

The `/s:build` skill's Q&A loop SHALL name the knowledge capture rubric, by
the path `${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`,
when a sub-agent question's answer or a mid-build user interjection carries
new information: the information is classified into exactly one of the four
tiers, with binding information updating the change's spec artifacts before
the answer is given (epic-scope binding information surfaced to the user
for the epic's amendment discipline, never applied as a free epic edit),
reference material installed through the emit engine and linked from the
epic's `## References` shelf, durable knowledge routed to the wiki or
oracle queue, and noise recorded nowhere. The harness build body SHALL
carry a compact consult sentence naming the four tiers and the rubric by
its `"$S/../../epic/references/` path at its question-answering moment, in
both its sub-agent and single-agent renderings.

#### Scenario: Build skill consults when answers carry knowledge
- **WHEN** `plugins/s/skills/build/SKILL.md`'s Q&A-loop phase is inspected
- **THEN** it directs classifying what an answer or mid-build interjection
  carries against the knowledge capture rubric by its plugin-root path,
  keeps update-the-artifacts-first as the binding tier's change-scope rule,
  and routes epic-scope binding information to the amendment discipline

#### Scenario: Harness build body mirrors the consult
- **WHEN** `plugins/s/harness/bodies/build.md` is rendered with and without
  the subagents feature
- **THEN** both renderings carry the consult sentence naming the four tiers
  and the rubric path, and each rendered body stays under the 120-line
  budget
