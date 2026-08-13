## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: 9fa5d0ee7b3e

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising, plus the solution
diagram whenever the user's request asked for one — as plain response text.
The investigation turn SHALL then end with a single **go-ahead dialog**: an
AskUserQuestion, issued only after the digest has been printed in that turn,
asking whether the findings and proposed shape are clear enough to proceed,
with options exactly — proceed to the depth gate and planning (recommended,
listed first), adjust scope first, or stop. The go-ahead dialog SHALL NOT
contain any planning decision, and no other AskUserQuestion and no depth-gate
verdict SHALL appear in the investigation turn; decision-resolving question
rounds follow in later turns, after the user's go-ahead. Internal reasoning
SHALL NOT substitute for the digest.

#### Scenario: Digest then go-ahead dialog close the turn
- **WHEN** investigation completes in a planning session
- **THEN** the turn carries the findings digest as response text followed by
  one go-ahead AskUserQuestion (proceed recommended first), and no other
  question dialog

#### Scenario: Go-ahead dialog carries no planning decisions
- **WHEN** the go-ahead dialog is issued
- **THEN** its options concern only proceeding, adjusting scope, or stopping
  — never architecture, content, or implementation choices

#### Scenario: Questions wait for the go-ahead
- **WHEN** the user answers the go-ahead dialog with proceed
- **THEN** the depth gate is announced and any decision-resolving rounds
  begin only in that or later turns, folding in whatever the response
  changed about scope

#### Scenario: Requested findings report is not skipped
- **WHEN** the user's request explicitly asks to be told what the
  investigation finds or to draw a diagram of the solution
- **THEN** the digest turn carries the findings and the requested diagram
  before the go-ahead dialog is issued
