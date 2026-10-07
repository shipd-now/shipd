## MODIFIED Requirements

### Requirement: Rubric consult in epic authoring
id: epic-authoring-rubric-consult
base: ece516e4fe17

The `/s:epic` skill SHALL name the knowledge capture rubric, by the path
`${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`, at the
moment question-round answers fold in: each substantive piece of arriving
information is classified into exactly one tier, with binding information
landing in the `## Decisions` section being authored, reference material
installed through the emit engine and linked from `## References`, durable
knowledge routed to the wiki or oracle queue, and noise deliberately
dropped. The harness epic body SHALL carry a compact consult sentence
naming the four tiers and the rubric by its `"$S/../../epic/references/`
path.

#### Scenario: Epic skill consults at the fold-in
- **WHEN** `plugins/s/skills/epic/SKILL.md`'s question-round flow is
  inspected
- **THEN** it directs classifying folded-in answers against the knowledge
  capture rubric by its plugin-root path and names all four tier
  destinations

#### Scenario: Harness epic body mirrors the consult
- **WHEN** `plugins/s/harness/bodies/epic.md` is inspected
- **THEN** its question-round section carries the consult sentence naming
  the four tiers and the rubric path, and the rendered body stays within
  the rendered-body size budget `harness-command-bodies` owns
