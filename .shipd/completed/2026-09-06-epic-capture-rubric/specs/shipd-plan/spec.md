## ADDED Requirements

### Requirement: Rubric consult at plan information arrival
id: plan-rubric-consult

The `/s:plan` skill SHALL name the knowledge capture rubric, by the path
`${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`, at its
information-arrival moments: where a typed question-round answer folds in,
the answer's substance is classified into exactly one of the rubric's four
tiers — binding into the change's own artifacts (or, at epic scope, flagged
for the epic's amendment discipline rather than a free epic edit),
reference through the emit engine onto the `## References` shelf, durable
to the wiki or oracle queue, noise nowhere — and the supplied-document
install rule SHALL identify itself as the rubric's reference tier. The
existing oracle-queue capture rule (classifying a queue-filed answer
against the capture durability rubric before any queue write) SHALL remain
authoritative for the durable tier's queue mechanics and SHALL NOT be
duplicated or contradicted by the consult. The harness plan body SHALL
carry a compact consult sentence naming the four tiers and the rubric by
its `"$S/../../epic/references/` path.

#### Scenario: Plan skill consults at the typed-answer fold-in
- **WHEN** `plugins/s/skills/plan/SKILL.md`'s question-round guidance is
  inspected
- **THEN** it directs classifying each folded-in answer against the
  knowledge capture rubric by its plugin-root path, names all four tier
  destinations, and leaves the oracle-queue capture rule in place for
  durable-tier queue writes

#### Scenario: Supplied documents are named as the reference tier
- **WHEN** the skill's supplied-documents rule is inspected
- **THEN** it identifies the docs-kind install-and-link path as the
  knowledge capture rubric's reference tier

#### Scenario: Harness plan body mirrors the consult
- **WHEN** `plugins/s/harness/bodies/plan.md` is inspected
- **THEN** its question-round step carries the consult sentence naming the
  four tiers and the rubric path, and the rendered body stays under the
  120-line budget
