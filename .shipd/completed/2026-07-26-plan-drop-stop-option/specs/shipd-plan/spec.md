## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: 6482bc27ac1a

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising, plus the solution
diagram whenever the user's request asked for one — as plain response text.
Because the harness can drop text sharing a turn with a dialog, the
investigation turn SHALL then end with a single **typed go-ahead prompt**:
a plain-text numbered prompt closing the digest's message, asking whether
the findings and proposed shape are clear enough to proceed, with options
exactly — proceed to the depth gate and planning (recommended, named
first), or adjust scope first — collected from the user's typed reply. No
AskUserQuestion SHALL be issued in the investigation turn. The go-ahead
prompt SHALL NOT contain any planning decision, and no depth-gate verdict
SHALL appear in the investigation turn; decision-resolving question rounds
follow in later turns, after the user's go-ahead. Internal reasoning SHALL
NOT substitute for the digest.

#### Scenario: Digest then typed go-ahead close the turn
- **WHEN** investigation completes in a planning session
- **THEN** the turn carries the findings digest as response text ending
  with one numbered go-ahead prompt (proceed recommended, named first),
  answered by typed reply, and no AskUserQuestion

#### Scenario: Go-ahead prompt offers exactly proceed and adjust
- **WHEN** the go-ahead prompt is offered
- **THEN** its options are exactly proceed and adjust-scope — no stop
  option, and never architecture, content, or implementation choices

#### Scenario: Questions wait for the go-ahead
- **WHEN** the user's typed reply to the go-ahead is proceed
- **THEN** the depth gate is announced and any decision-resolving rounds
  begin only in that or later turns, folding in whatever the response
  changed about scope

#### Scenario: Requested findings report is not skipped
- **WHEN** the user's request explicitly asks to be told what the
  investigation finds or to draw a diagram of the solution
- **THEN** the digest turn carries the findings and the requested diagram
  before the go-ahead prompt is offered
