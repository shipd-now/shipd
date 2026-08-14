## MODIFIED Requirements

### Requirement: Context brief before question rounds
id: context-brief
base: b1a5570e235a

When the skill is about to issue a decision-resolving AskUserQuestion round —
the fast path's batched call or a depth-path round — it SHALL first present a
context brief: a restatement of the accumulated understanding, a diagram only
where one carries the decisions being asked, and the list of open decisions
the round will settle, with the AskUserQuestion call issued in the same turn.
The brief SHALL be user-visible response text, never only internal reasoning,
and it is a precondition of the call: a decision-resolving AskUserQuestion
whose turn did not first present the visible brief is a protocol violation.
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

#### Scenario: Question without a visible brief is a violation
- **WHEN** the skill is about to issue a decision-resolving AskUserQuestion
  and no user-visible brief has been presented in that turn
- **THEN** the call is not issued until the brief is printed as response text

#### Scenario: Chain follow-up gets a delta line, not a recap
- **WHEN** a dependent chain's next question follows an answer
- **THEN** it is prefaced by one line stating what that answer changed, not a
  full restatement

### Requirement: Visualization on demand
id: visualization-on-demand
base: da2cb243f21c

Where a diagram or comparison table would clarify a decision being put to the
user, the skill SHALL load the visualization reference (at most once per
session) and attach the visual to the question — as an ASCII diagram, an
options table, or an AskUserQuestion option preview. The skill SHALL NOT emit
visuals that do not carry a decision, except that when the user's request
explicitly asks for a diagram or visual, that request satisfies the
carries-a-decision bar by itself: the skill SHALL honor it, presenting the
requested solution diagram no later than the first context brief (or in the
findings digest when no question round occurs).

#### Scenario: Diagram accompanies an architectural choice
- **WHEN** a depth-path question puts two candidate architectures to the user
- **THEN** the question carries a visual comparison of the candidates

#### Scenario: No decorative diagrams
- **WHEN** a decision is clear from one sentence of prose and the user asked
  for no visual
- **THEN** the skill asks it without loading the visualization reference

#### Scenario: Explicit diagram request is honored
- **WHEN** the user's request says to draw a diagram of the potential solution
- **THEN** a solution diagram appears no later than the first context brief,
  regardless of whether any pending decision needs a visual

## ADDED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising — as plain response
text, before announcing the depth-gate verdict and before any
AskUserQuestion call in the session. Internal reasoning SHALL NOT substitute
for the digest.

#### Scenario: Digest precedes the gate and any questions
- **WHEN** investigation completes in a planning session
- **THEN** a findings digest is printed as response text before the
  depth-gate verdict is announced and before any question dialog appears

#### Scenario: Requested findings report is not skipped
- **WHEN** the user's request explicitly asks to be told what the
  investigation finds
- **THEN** the digest addresses that request directly rather than being
  folded into internal reasoning

### Requirement: Missing-layout guard
id: missing-layout-guard

When the repository lacks the `am/` layout, the skill SHALL stop before any
questioning, report the missing layout, and ask via one AskUserQuestion
whether to scaffold the minimal layout (`am/verified/`, `am/planned/`,
`am/completed/`) and continue, or stop; it SHALL NOT continue planning as
though the layout existed.

#### Scenario: Missing layout stops the flow
- **WHEN** `/s:plan` runs in a repository with no `am/` directory
- **THEN** the skill reports the missing layout and asks scaffold-or-stop
  before any planning question is posed

#### Scenario: Accepted scaffold proceeds
- **WHEN** the user accepts the scaffold option
- **THEN** the skill creates the three empty directories and continues the
  normal flow
