## ADDED Requirements

### Requirement: Context brief before question rounds
id: context-brief

When the skill is about to issue a decision-resolving AskUserQuestion round —
the fast path's batched call or a depth-path round — it SHALL first present a
context brief: a restatement of the accumulated understanding, a diagram only
where one carries the decisions being asked, and the list of open decisions
the round will settle, with the AskUserQuestion call issued in the same turn.
The confirm-gated shared-understanding summary SHALL NOT require a preceding
brief. Within a dependent chain, follow-up questions SHALL be prefaced by a
one-line statement of what the previous answer changed rather than a full
brief.

#### Scenario: Fast-path batched call is prefaced by a brief
- **WHEN** the fast path has un-inferrable decisions and issues its single
  batched AskUserQuestion call
- **THEN** the same turn first presents what is already known and the list of
  open decisions, and only then the question dialog

#### Scenario: Depth-path round is prefaced by a brief
- **WHEN** a depth-path round is about to put grouped decisions to the user
- **THEN** the round opens with the accumulated understanding — including a
  diagram when one carries the decisions — and ends with the grouped
  AskUserQuestion call

#### Scenario: Chain follow-up gets a delta line, not a recap
- **WHEN** a dependent chain's next question follows an answer
- **THEN** it is prefaced by one line stating what that answer changed, not a
  full restatement

## MODIFIED Requirements

### Requirement: Batched user questions on the fast path
id: batched-user-questions
base: f2af5602e3ba

While on the fast path, when decisions remain that the skill cannot infer, it
SHALL batch them into a single AskUserQuestion call of two to four focused
questions, each with concrete options and a recommended default listed first,
and SHALL NOT drip questions one at a time across multiple turns. This
batching contract SHALL NOT apply on the depth path, where the grill loop's
grouped-round protocol governs instead.

#### Scenario: Un-inferrable decisions are batched
- **WHEN** the fast path leaves three genuinely open decisions after
  investigation
- **THEN** the skill issues one AskUserQuestion call containing all three, each
  with concrete options and a recommended default first

#### Scenario: No questions when context suffices
- **WHEN** the user's request plus the codebase already satisfy the readiness
  checklist
- **THEN** the skill proceeds to emission without asking the user anything

#### Scenario: Depth path is exempt from batching
- **WHEN** the depth gate has selected the depth path
- **THEN** questions follow the grill loop's grouped-round protocol — not this
  contract's single fixed batch

### Requirement: Bounded grill loop on the depth path
id: grill-loop
base: 242fd75455f0

While on the depth path, the skill SHALL load the dialogue reference, derive
the agenda of open task-shaping decisions, and partition it: decisions whose
framing does not depend on another answer SHALL be grouped into a single
AskUserQuestion call of up to four questions, each with its recommended option
listed first; decisions whose question cannot be phrased until an earlier
answer lands SHALL be asked one at a time in dependency order. When unsure
whether a decision is independent, the skill SHALL treat it as dependent.
Discoverable facts SHALL be read from the repository, never asked. The loop
SHALL end when no open decision would change the task list. If the agenda of
open decisions exceeds roughly six, then the skill SHALL suggest decomposing
the change via `/s:epic` rather than continuing the interview.

#### Scenario: Independent decisions are grouped into one call
- **WHEN** the depth path has three open decisions whose framing does not
  depend on each other's answers
- **THEN** the skill asks all three in a single AskUserQuestion call, each
  with a recommended option first

#### Scenario: Dependent chain is resolved one at a time
- **WHEN** the question for decision B cannot be phrased until decision A is
  answered
- **THEN** the skill asks A first and poses B in a later round shaped by A's
  answer

#### Scenario: Loop terminates at readiness
- **WHEN** the last open decision that would change the task list is resolved
- **THEN** the skill stops asking and proceeds toward emission

#### Scenario: Oversized agenda suggests decomposition
- **WHEN** the agenda of open task-shaping decisions grows past roughly six
- **THEN** the skill suggests `/s:epic` instead of continuing the interview
