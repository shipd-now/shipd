## MODIFIED Requirements

### Requirement: Oracle consultation before user question rounds
id: oracle-consultation
base: b3e8fab6dd09

When genuinely un-inferrable task-shaping decisions remain and a user question
round would otherwise open — the investigation turn's round, a depth-path
round, or enrichment's true-gap round — the skill SHALL first shape each
remaining decision into a compact question (the decision, concrete options,
and the skill's recommended default) and consult the `s:oracle` agent with
one spawn per decision, passing the compact question, the asking repo's
absolute root, and the status CLI path. The skill SHALL branch on the
verdict's first non-blank line: a decision answered `ANSWER` SHALL be folded
in as resolved and SHALL NOT be put to the user, while a decision returned
`INSUFFICIENT` SHALL proceed to the user round unchanged. If a verdict's
first line is `ANSWER` but its body lacks a `Cited:` line or an `Evidence:`
line, then the skill SHALL treat that decision as `INSUFFICIENT`. If a spawn
fails or the verdict's first line is neither `ANSWER` nor `INSUFFICIENT`,
then the skill SHALL treat that decision as `INSUFFICIENT` and continue — the
consultation SHALL never block planning. When the findings digest leaves open
task-shaping decisions, the skill SHALL consult the rung in that same turn, so
the digest, the consultation, and the round for the `INSUFFICIENT` remainder
form a single message exchange.

#### Scenario: Wiki-held answers skip the user round
- **WHEN** every remaining un-inferrable decision comes back `ANSWER`
- **THEN** the skill proceeds toward the readiness gate without opening a
  user question round

#### Scenario: Insufficient decisions still go to the user
- **WHEN** the oracle returns `INSUFFICIENT` for a decision
- **THEN** that decision appears in the user question round exactly as it
  would have without the rung

#### Scenario: Uncited answer is demoted
- **WHEN** a verdict's first line is `ANSWER` but its body carries no
  `Cited:` line or no `Evidence:` line
- **THEN** the skill treats that decision as `INSUFFICIENT` and it proceeds
  to the user round

#### Scenario: A failed spawn degrades instead of blocking
- **WHEN** an oracle spawn errors or returns a first line that is neither
  `ANSWER` nor `INSUFFICIENT`
- **THEN** the skill treats that decision as `INSUFFICIENT` and the flow
  continues without error

#### Scenario: The digest's open questions are consulted in that turn
- **WHEN** the findings digest names open task-shaping questions
- **THEN** the oracle is consulted on them before the turn ends, rather than
  deferred to a later turn

## ADDED Requirements

### Requirement: Typed answers are captured for the oracle
id: typed-answer-capture

When a typed user round resolves a decision the oracle returned
`INSUFFICIENT` with a filed `q-<slug>` (a `Queued:` line naming a slug rather
than `none`), the skill SHALL distill the typed resolution into a concise
durable answer and write it through `spec_status.py wiki-queue-answer <slug>
--answer "<text>"` before emission, in addition to ledgering the consultation
in `plan.md`'s `## Questions and answers` section. Where the verdict reported
`Queued: none`, the skill SHALL skip the capture and state that nothing
durable was written. If the capture write fails, then the skill SHALL report
the failure and continue — capture SHALL never block planning.

#### Scenario: Typed resolution reaches the queue block
- **GIVEN** an `INSUFFICIENT` verdict whose `Queued:` line names `q-<slug>`
- **WHEN** the user's typed reply resolves that decision
- **THEN** the skill writes the distilled answer via `wiki-queue-answer`
  before emission and the ledger entry records the resolution

#### Scenario: No workspace skips capture
- **GIVEN** an `INSUFFICIENT` verdict whose `Queued:` line reads `none`
- **WHEN** the user's typed reply resolves that decision
- **THEN** the skill skips the capture, states that nothing durable was
  written, and planning proceeds

#### Scenario: Capture failure does not block emission
- **WHEN** the `wiki-queue-answer` write exits non-zero
- **THEN** the skill reports the failure and the flow continues to emission
