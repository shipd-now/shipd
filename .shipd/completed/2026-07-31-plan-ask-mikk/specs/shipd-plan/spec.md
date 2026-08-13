## ADDED Requirements

### Requirement: Oracle consultation before user question rounds
id: oracle-consultation

When genuinely un-inferrable task-shaping decisions remain and a user question
round would otherwise open — the fast path's batched round, a depth-path
round, or enrichment's true-gap round — the skill SHALL first shape each
remaining decision into a compact question (the decision, concrete options,
and the skill's recommended default) and consult the `s:oracle` agent with
one spawn per decision, passing the compact question, the asking repo's
absolute root, and the status CLI path. The skill SHALL branch on the
verdict's first non-blank line: a decision answered `ANSWER` SHALL be folded
in as resolved and SHALL NOT be put to the user, while a decision returned
`INSUFFICIENT` SHALL proceed to the user round unchanged. If a spawn fails or
the verdict's first line is neither `ANSWER` nor `INSUFFICIENT`, then the
skill SHALL treat that decision as `INSUFFICIENT` and continue — the
consultation SHALL never block planning. The skill SHALL NOT consult the
oracle in the investigation turn: open questions displayed by the findings
digest reach the rung only in the post-gate rounds.

#### Scenario: Wiki-held answers skip the user round
- **WHEN** every remaining un-inferrable decision comes back `ANSWER`
- **THEN** the skill proceeds toward the readiness gate without opening a
  user question round

#### Scenario: Insufficient decisions still go to the user
- **WHEN** the oracle returns `INSUFFICIENT` for a decision
- **THEN** that decision appears in the user question round exactly as it
  would have without the rung

#### Scenario: A failed spawn degrades instead of blocking
- **WHEN** an oracle spawn errors or returns a first line that is neither
  `ANSWER` nor `INSUFFICIENT`
- **THEN** the skill treats that decision as `INSUFFICIENT` and the flow
  continues without error

#### Scenario: Investigation turn stays oracle-free
- **WHEN** the investigation digest ends on an OPEN QUESTIONS list
- **THEN** no oracle spawn has occurred in that turn, and those questions are
  consulted only when a post-gate round would open

### Requirement: Oracle-settled decisions stay visible
id: oracle-resolution-visibility

When the oracle settles one or more decisions, the skill SHALL report each
settled decision in user-visible text with the oracle's position and its
`Cited:` source(s) — in the round's context brief when a round still opens
for the remaining decisions, or in the status text before proceeding when
nothing remains to ask. If the user's typed reply contradicts an
oracle-settled decision, then the user's choice SHALL govern.

#### Scenario: Partially settled agenda is reported in the brief
- **WHEN** the oracle answers some decisions and a round opens for the rest
- **THEN** the context brief lists each oracle-settled decision with its
  position and citations before the numbered questions

#### Scenario: Fully settled agenda is reported before proceeding
- **WHEN** the oracle answers every remaining decision and no round opens
- **THEN** the skill states the settled decisions and their citations in
  visible status text before moving to the readiness gate

#### Scenario: User override beats the oracle
- **WHEN** the user's typed reply contradicts a decision the oracle settled
- **THEN** the plan follows the user's choice, not the oracle's answer
