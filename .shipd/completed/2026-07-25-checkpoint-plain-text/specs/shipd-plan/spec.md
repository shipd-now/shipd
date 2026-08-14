## MODIFIED Requirements

### Requirement: Context brief before question rounds
id: context-brief
base: 59538bc2d72a

When the skill is about to put a decision-resolving question round to the
user — the fast path's batched round or a depth-path round — it SHALL first
present a context brief: a restatement of the accumulated understanding, a
diagram only where one carries the decisions being asked, and the list of
open decisions the round will settle. The brief SHALL be user-visible
response text, never only internal reasoning, and it is a precondition of
the round. Because the harness can drop text sharing a turn with a dialog,
the round SHALL be collected as a typed reply: the brief's turn ends with
the decisions as plain-text numbered questions, each with concrete options
and the recommended default named first, and no AskUserQuestion SHALL be
issued in that turn. AskUserQuestion MAY be used only for a self-contained
question in a turn carrying no brief or other substantive prose. Within a
dependent chain, follow-up questions SHALL be prefaced by a one-line
statement of what the previous answer changed rather than a full brief.

#### Scenario: Brief and typed round form one message
- **WHEN** the skill has un-inferrable decisions and issues a
  decision-resolving round
- **THEN** one plain-text message presents what is already known, the open
  decisions, and the numbered questions with options, and the answers are
  collected from the user's typed reply

#### Scenario: No dialog shares a turn with a brief
- **WHEN** a context brief has been presented in the current turn
- **THEN** no AskUserQuestion is issued in that turn; the round is typed

#### Scenario: Dialog allowed only without substantive prose
- **WHEN** a single self-contained question needs no brief and its turn
  carries no other substantive prose
- **THEN** an AskUserQuestion dialog may collect it

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: fad2f0c5bd79

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising, plus the solution
diagram whenever the user's request asked for one — as plain response text.
Because the harness can drop text sharing a turn with a dialog, the
investigation turn SHALL then end with a single **typed go-ahead prompt**:
a plain-text numbered prompt closing the digest's message, asking whether
the findings and proposed shape are clear enough to proceed, with options
exactly — proceed to the depth gate and planning (recommended, named
first), adjust scope first, or stop — collected from the user's typed
reply. No AskUserQuestion SHALL be issued in the investigation turn. The
go-ahead prompt SHALL NOT contain any planning decision, and no depth-gate
verdict SHALL appear in the investigation turn; decision-resolving question
rounds follow in later turns, after the user's go-ahead. Internal reasoning
SHALL NOT substitute for the digest.

#### Scenario: Digest then typed go-ahead close the turn
- **WHEN** investigation completes in a planning session
- **THEN** the turn carries the findings digest as response text ending
  with one numbered go-ahead prompt (proceed recommended, named first),
  answered by typed reply, and no AskUserQuestion

#### Scenario: Go-ahead prompt carries no planning decisions
- **WHEN** the go-ahead prompt is offered
- **THEN** its options concern only proceeding, adjusting scope, or stopping
  — never architecture, content, or implementation choices

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
