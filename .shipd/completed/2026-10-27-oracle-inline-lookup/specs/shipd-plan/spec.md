## MODIFIED Requirements

### Requirement: Oracle consultation before user question rounds
id: oracle-consultation
base: 2bc4006b4c82
Dropped: A failed spawn degrades instead of blocking

When genuinely un-inferrable task-shaping decisions remain and a user question
round would otherwise open — the investigation turn's round, a depth-path
round, or enrichment's true-gap round — the skill SHALL first shape each
remaining decision into a compact question (the decision, concrete options,
and the skill's recommended default) and consult the oracle inline per the
oracle consultation contract
(`plugins/s/skills/ask/references/oracle-contract.md`): one `spec_status.py
oracle-lookup` run per decision, whose output the skill judges itself,
spawning no agent. The skill SHALL branch on each verdict's first line: a
decision answered `ANSWER` with no `Authority: advisory` line SHALL be folded
in as resolved and SHALL NOT be put to the user, while a decision judged
`INSUFFICIENT` SHALL be queued per the contract and SHALL proceed to the user
round unchanged. Where an `ANSWER` carries an `Authority: advisory` line, the
decision SHALL still enter the user round, with the advisory position
presented as the recommended first option and its citation named — the
advisory answer recommends, it never settles. If an `ANSWER` lacks a
`Cited:` line or an `Evidence:` line, then the skill SHALL treat that
decision as `INSUFFICIENT`. If the lookup exits non-zero, then the skill
SHALL treat that decision as `INSUFFICIENT` and continue — the consultation
SHALL never block planning. When the findings digest leaves open
task-shaping decisions, the skill SHALL consult the rung in that same turn,
so the digest, the consultation, and the round for the `INSUFFICIENT`
remainder form a single message exchange.

#### Scenario: Wiki-held answers skip the user round
- **WHEN** every remaining un-inferrable decision is judged `ANSWER`
  without an `Authority: advisory` line
- **THEN** the skill proceeds toward the readiness gate without opening a
  user question round

#### Scenario: Advisory answer still reaches the user
- **WHEN** a decision is judged `ANSWER` carrying `Authority: advisory`
- **THEN** the decision appears in the user question round with the
  advisory position as the recommended first option, cited

#### Scenario: Insufficient decisions still go to the user
- **WHEN** a decision is judged `INSUFFICIENT`
- **THEN** it is queued and appears in the user question round exactly as
  it would have without the rung

#### Scenario: Uncited answer is demoted
- **WHEN** an `ANSWER` carries no `Cited:` line or no `Evidence:` line
- **THEN** the skill treats that decision as `INSUFFICIENT` and it proceeds
  to the user round

#### Scenario: A failed lookup degrades instead of blocking
- **WHEN** an `oracle-lookup` run exits non-zero
- **THEN** the skill treats that decision as `INSUFFICIENT` and the flow
  continues without error

#### Scenario: No agent is spawned
- **WHEN** `plugins/s/skills/plan/SKILL.md`'s oracle rung is inspected
- **THEN** it directs running `oracle-lookup` per the contract reference and
  names no `s:oracle` agent

#### Scenario: The digest's open questions are consulted in that turn
- **WHEN** the findings digest names open task-shaping questions
- **THEN** the oracle is consulted on them before the turn ends, rather than
  deferred to a later turn
