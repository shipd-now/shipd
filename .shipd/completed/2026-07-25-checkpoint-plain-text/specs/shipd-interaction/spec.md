## ADDED Requirements

### Requirement: Dialog and prose separation
id: dialog-prose-separation

The harness can drop or hide assistant text that shares a turn with an
AskUserQuestion call, so a turn that issues an AskUserQuestion SHALL carry no
load-bearing prose outside the dialog — at most a one-line lead-in. Content
the user must read to answer (context briefs, lessons, summaries) SHALL
either be carried inside the dialog's own fields (question text, option
labels and descriptions) or SHALL end its turn as plain text with the
choices offered as a numbered list and the answer collected as a typed
reply, with the recommended default named.

#### Scenario: Substantive prose ends the turn as plain text
- **WHEN** a skill must present an explanation, brief, or lesson and then
  collect a decision
- **THEN** the explanation and a numbered plain-text prompt form one
  message answered by typing, and no AskUserQuestion is issued in that turn

#### Scenario: Dialogs appear only in prose-free turns
- **WHEN** a skill issues an AskUserQuestion
- **THEN** the turn's visible text outside the dialog is at most a one-line
  lead-in, with all decision context inside the dialog's fields
