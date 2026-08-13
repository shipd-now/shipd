## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: 383e6666147e

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising, plus the solution
diagram whenever the user's request asked for one — as plain response text,
and the digest SHALL be the final message of the investigation turn: the
skill SHALL end its turn there and wait for the user's go-ahead. The
investigation turn SHALL NOT contain an AskUserQuestion call or a depth-gate
verdict; both follow in later turns, after the user has responded to the
digest. Internal reasoning SHALL NOT substitute for the digest.

#### Scenario: Digest is a hard checkpoint
- **WHEN** investigation completes in a planning session
- **THEN** the turn ends with the findings digest as its final message, with
  no AskUserQuestion call issued in that turn

#### Scenario: Questions wait for the go-ahead
- **WHEN** the user responds to the digest
- **THEN** the depth gate is announced and any question rounds begin only in
  that or later turns, folding in whatever the response changed about scope

#### Scenario: Requested findings report is not skipped
- **WHEN** the user's request explicitly asks to be told what the
  investigation finds or to draw a diagram of the solution
- **THEN** the digest turn carries the findings and the requested diagram
  before any question is posed
