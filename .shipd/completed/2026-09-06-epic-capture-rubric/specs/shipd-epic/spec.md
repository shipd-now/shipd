## ADDED Requirements

### Requirement: Knowledge capture rubric
id: knowledge-capture-rubric

The plugin SHALL provide a knowledge capture rubric reference at
`plugins/s/skills/epic/references/capture-rubric.md` defining four tiers for
routing information that arrives during planning, building, or epic
authoring: **binding** (changes what executors do — the change's own
artifacts at change scope; at epic scope the epic's `## Decisions`, changed
only through the sanctioned amendment discipline of a fresh
`epic-amend-<slug>` worktree, a dated provenance line on the amended
Decision, and a lint-gated pull request, never a free edit), **reference**
(supports the feature without binding executors — installed through the
emit engine's document kinds and linked from the epic's `## References`
shelf, or cited in `plan.md` prose when no epic resolves), **durable**
(outlives the feature — routed to the workspace wiki via `/s:teach` or the
oracle queue, where the capture durability rubric at
`plugins/s/skills/ask/references/capture-rubric.md` governs the queue
write), and **noise** (recorded nowhere, deliberately). The rubric SHALL
name itself the "knowledge capture rubric", SHALL explicitly distinguish
itself from the capture durability rubric and name the durable tier's
handoff to it without duplicating its tiers, SHALL carry a calibrated
examples table of at least eight rows with at least two per tier, and SHALL
carry tie-breakers covering at least: binding versus reference decided by
obeyed-versus-consulted, reference versus durable decided by the feature's
lifetime, borderline cases leaning toward the less-capturing tier, and the
binding tier's home decided by scope. The rubric SHALL NOT reference any
unshipped verb, flag, or skill argument.

#### Scenario: Rubric reference exists with four tiers
- **WHEN** `plugins/s/skills/epic/references/capture-rubric.md` is inspected
- **THEN** it defines the binding, reference, durable, and noise tiers, each
  with its destination, and names the epic-scope amendment discipline for
  the binding tier

#### Scenario: Durable tier hands off to the durability rubric
- **WHEN** the rubric's durable tier is inspected
- **THEN** it routes to the workspace wiki or oracle queue and names
  `plugins/s/skills/ask/references/capture-rubric.md` as governing the
  queue write, and the include/exclude/consent-gated tiers are not
  restated as the knowledge capture rubric's own

#### Scenario: Calibrated examples and tie-breakers are present
- **WHEN** the rubric's examples table and tie-breakers are inspected
- **THEN** the table holds at least eight rows spanning all four tiers with
  at least two rows per tier, each with a rationale, and each named
  tie-breaker appears

### Requirement: Rubric consult in epic authoring
id: epic-authoring-rubric-consult

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
  the four tiers and the rubric path, and the rendered body stays under the
  120-line budget
