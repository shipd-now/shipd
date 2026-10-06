## MODIFIED Requirements

### Requirement: Onboard tour skill
id: onboard-tour-skill
base: 3f9a9a7bc540

An `/s:onboard` skill SHALL teach through a fixed nine-step walkthrough:
(1) what Spec-Driven Development is, in one paragraph; (2) how shipd
works — it creates artifacts and executes in worktrees, briefly explained,
enabling many changes in parallel; (3) the artifacts as short dot points;
(4) the example `plan.md`; (5) the example delta spec; (6) the example
tasks plus the model-tiering approach — the best model plans and the
second-best executes, for efficiency, speed, and cost; (7) a pause that
summarizes what was learned; (8) implementing the tasks and building the
kanban board, ending with what was built and how to test it in the shell;
(9) a suggested small enhancement with the exact copy/paste command to plan
it. On a fresh start the first visible output SHALL be the shipd ASCII
banner — carried verbatim in the skill, byte-identical to the `wordmark`
module's `ART` constant — in a fenced code block above the greeting. The
skill SHALL NOT present a chapter menu or any start-choice, and SHALL NOT
depend on a chapter library.

#### Scenario: Banner opens a fresh start
- **WHEN** `/s:onboard` starts fresh
- **THEN** the first visible output is the shipd ASCII banner in a fenced
  code block, followed by the greeting and step 1

#### Scenario: Onboard banner matches the wordmark art
- **WHEN** the lines inside the skill's step-1 fenced banner block are
  compared to `wordmark.ART`
- **THEN** they are byte-identical

#### Scenario: Steps follow the fixed order
- **WHEN** the user advances with `next` from step 1 onward
- **THEN** the steps render in the fixed order — SDD, how shipd works,
  artifact dot points, plan.md, spec, tasks, summary, implement, enhancement
  handoff

#### Scenario: Model tiering is taught
- **WHEN** step 6 renders
- **THEN** it explains that shipd plans on the best model and executes
  tasks on the second-best for efficiency, speed, and cost
