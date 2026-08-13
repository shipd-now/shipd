## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: e4f036f04196

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising, plus the solution
diagram whenever the user's request asked for one — as plain response text.
The investigation turn SHALL end in exactly one of two mutually exclusive
ways. When investigation leaves one or more genuinely open task-shaping
questions, the digest SHALL end on an `OPEN QUESTIONS` header listing them —
with no go-ahead prompt and no clear-enough-to-proceed phrasing; the
questions are displayed, not asked, and the user's next typed message
(answers, corrections, or a bare go-ahead) is folded in, with any remaining
questions settled in the post-gate decision rounds. When no such question
exists, the digest SHALL instead end on a single **typed go-ahead prompt** —
a plain-text numbered prompt asking whether the findings and proposed shape
are clear enough to proceed, with options exactly: proceed to the depth gate
and planning (recommended, named first), or adjust scope first — collected
from the user's typed reply (a dialog is not used because the harness can
drop text sharing a turn with one). No AskUserQuestion SHALL be issued in
the investigation turn, neither ending SHALL contain any planning decision,
and no depth-gate verdict SHALL appear in the investigation turn;
decision-resolving question rounds follow in later turns, after the user's
response. Internal reasoning SHALL NOT substitute for the digest.

#### Scenario: Open questions end the turn without a go-ahead prompt
- **WHEN** investigation leaves a task-shaping question only the user can
  settle
- **THEN** the digest ends on the `OPEN QUESTIONS` list with no
  proceed/adjust block and no clear-enough-to-proceed phrasing, and the
  turn ends there

#### Scenario: No open questions ends the turn on the go-ahead prompt
- **WHEN** investigation leaves no genuinely open task-shaping question
- **THEN** the digest ends on the numbered go-ahead prompt (proceed
  recommended, named first; adjust scope as the alternative) with no
  `OPEN QUESTIONS` header, answered by typed reply, and no AskUserQuestion

#### Scenario: Answers to open questions serve as the go-ahead
- **WHEN** the user's next message answers some or all listed open questions
- **THEN** the answers are folded into the understanding, the depth gate is
  announced in that or later turns, and any still-open questions carry into
  the post-gate decision rounds

#### Scenario: Requested findings report is not skipped
- **WHEN** the user's request explicitly asks to be told what the
  investigation finds or to draw a diagram of the solution
- **THEN** the digest turn carries the findings and the requested diagram
  before either ending is offered
