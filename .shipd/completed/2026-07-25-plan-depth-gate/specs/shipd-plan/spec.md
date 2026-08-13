## ADDED Requirements

### Requirement: Depth gate after investigation
id: depth-gate

When investigation completes, the `am:plan` skill SHALL classify the change as
fast-path or depth-path by counting explicit signals — multiple viable
approaches whose choice changes the task list; an outcome-shaped rather than
mechanism-shaped request; a new capability being added; blast radius spanning
multiple capabilities; uncertainty language in the request — selecting the
depth path at two or more signals and the fast path otherwise. If the request
contains an explicit depth override (e.g. "grill me") or fast override (e.g.
"just plan it"), then the skill SHALL honor the override regardless of the
signal count. The skill SHALL announce the selected mode to the user in one
sentence.

#### Scenario: Complex change trips the gate
- **WHEN** investigation surfaces two viable architectures whose choice changes
  the task list and the request describes an outcome rather than a mechanism
- **THEN** the skill announces depth mode and enters the grill loop instead of
  issuing a single batched question call

#### Scenario: Simple change stays on the fast path
- **WHEN** investigation finds one obvious approach for a mechanism-shaped
  request touching one existing capability
- **THEN** the skill proceeds on the fast path with at most one batched
  question call and loads no dialogue reference

#### Scenario: User override beats the signal count
- **WHEN** the request says "just plan it" but the signal count is two or more
- **THEN** the skill takes the fast path

### Requirement: Bounded grill loop on the depth path
id: grill-loop

While on the depth path, the skill SHALL load the dialogue reference and
resolve the open task-shaping decisions one at a time, each via a single
AskUserQuestion call whose recommended option is listed first, reading
discoverable facts from the repository instead of asking about them. The loop
SHALL end when no open decision would change the task list. If the agenda of
open decisions exceeds roughly six, then the skill SHALL suggest decomposing
the change via `/s:epic` rather than continuing the interview.

#### Scenario: Decisions are resolved one at a time
- **WHEN** the depth path has three open task-shaping decisions
- **THEN** the skill asks three separate single-question AskUserQuestion calls,
  each with a recommended option first, folding each answer in before the next

#### Scenario: Loop terminates at readiness
- **WHEN** the last open decision that would change the task list is resolved
- **THEN** the skill stops asking and proceeds toward emission

#### Scenario: Oversized agenda suggests decomposition
- **WHEN** the agenda of open task-shaping decisions grows past roughly six
- **THEN** the skill suggests `/s:epic` instead of continuing the interview

### Requirement: Visualization on demand
id: visualization-on-demand

Where a diagram or comparison table would clarify a decision being put to the
user, the skill SHALL load the visualization reference (at most once per
session) and attach the visual to the question — as an ASCII diagram, an
options table, or an AskUserQuestion option preview. The skill SHALL NOT emit
visuals that do not carry a decision.

#### Scenario: Diagram accompanies an architectural choice
- **WHEN** a depth-path question puts two candidate architectures to the user
- **THEN** the question carries a visual comparison of the candidates

#### Scenario: No decorative diagrams
- **WHEN** a decision is clear from one sentence of prose
- **THEN** the skill asks it without loading the visualization reference

### Requirement: Shared-understanding summary closes the depth path
id: shared-understanding-summary

When the grill loop ends, the skill SHALL present a shared-understanding
summary — the problem, the chosen approach, each decision with a one-line
rationale, and known risks — and SHALL obtain the user's confirmation, with
"emit" as the recommended option, before proceeding to emission. The fast path
SHALL NOT add this step.

#### Scenario: Depth path confirms before emitting
- **WHEN** the grill loop resolves its last open decision
- **THEN** the skill presents the summary and waits for confirmation before
  authoring any artifact

#### Scenario: Fast path emits without a summary step
- **WHEN** the fast path satisfies the readiness checklist
- **THEN** the skill proceeds directly to silent emission

## MODIFIED Requirements

### Requirement: Batched user questions on the fast path
id: batched-user-questions
base: 0502d776de2d

While on the fast path, when decisions remain that the skill cannot infer, it
SHALL batch them into a single AskUserQuestion call of two to four focused
questions, each with concrete options and a recommended default listed first,
and SHALL NOT drip questions one at a time across multiple turns. This
batching contract SHALL NOT apply on the depth path, where the grill loop's
one-decision-per-question protocol governs instead.

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
- **THEN** questions follow the grill loop's one-at-a-time protocol, not the
  batching contract
