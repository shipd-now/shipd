# shipd-interaction

### Requirement: Question rejection recovery
id: question-rejection-recovery

If an AskUserQuestion call returns a rejection or interruption instead of a
selected answer, then the skill session SHALL treat it as a harness misfire
rather than a user decision: it SHALL NOT record a decline or a stop, and on
the user's next message it SHALL either fold in a typed answer or re-offer
the same choices as a plain-text numbered list and wait. An explicit stop —
a selected Stop option or a typed stop — SHALL still be honored immediately.
Every interactive shipd skill's SKILL.md (plan, build, epic, initiative,
status, onboard, research, forget, doctor) SHALL carry this recovery rule.

#### Scenario: Rejected question is re-offered, not obeyed
- **WHEN** an AskUserQuestion at a decision point comes back as a tool
  rejection and the user's next message does not answer it
- **THEN** the skill re-offers the same choices as a plain-text numbered
  list and waits, instead of treating the flow as declined or stopped

#### Scenario: Typed answer after a misfire is folded in
- **WHEN** an AskUserQuestion comes back rejected and the user's next
  message states one of the offered choices in plain text
- **THEN** the skill accepts that answer and continues as if the dialog had
  returned it

#### Scenario: Explicit stop still stops
- **WHEN** the user selects a Stop option or types that they want to stop
- **THEN** the skill honors it immediately

#### Scenario: All interactive skills carry the rule
- **WHEN** the nine interactive SKILL.md files are inspected
- **THEN** each contains the question rejection recovery rule

### Requirement: Dialog and prose separation
id: dialog-prose-separation

The harness can drop or hide assistant text that shares a turn with an
AskUserQuestion call, so a turn that issues an AskUserQuestion SHALL carry no
load-bearing prose outside the dialog — at most a one-line lead-in. An
AskUserQuestion dialog SHALL carry exactly one question, and only when that
question's brief fits in its question text and option descriptions. A round
of more than one question, or a question whose brief runs past one line,
SHALL end its turn as plain text with the briefs and a numbered list of
choices, the recommended default named, and the answer collected as a typed
reply.

#### Scenario: Substantive prose ends the turn as plain text
- **WHEN** a skill must present an explanation, brief, or lesson and then
  collect a decision
- **THEN** the explanation and a numbered plain-text prompt form one
  message answered by typing, and no AskUserQuestion is issued in that turn

#### Scenario: Dialogs appear only in prose-free turns
- **WHEN** a skill issues an AskUserQuestion
- **THEN** the turn's visible text outside the dialog is at most a one-line
  lead-in, with all decision context inside the dialog's fields

#### Scenario: Several questions take a typed round
- **WHEN** a skill has two or more decisions to ask in one round
- **THEN** it asks them as one numbered typed round with a brief per
  question, and issues no AskUserQuestion

### Requirement: Question brief
id: question-brief

Every question a shipd skill puts to the user SHALL open with a brief in
four parts, in order: the decision stated in plain words; why it matters,
naming what the feature does and what the answer changes; one concrete
example, left out only when the decision has no concrete instance; and the
options, the recommended one first and marked recommended, each saying what
choosing it causes. The reference
`plugins/s/skills/document/references/question-brief.md` SHALL define the
brief with worked examples, and SHALL carry the `reference` doc-type marker.
Every `plugins/s/skills/*/SKILL.md` that mentions `AskUserQuestion`, and the
harness body of each such skill, SHALL point to that reference by path.

#### Scenario: A grill question carries its brief
- **WHEN** the epic-grill final round asks which `--state` a `--task`
  reply defaults to
- **THEN** the question states what `shipd room message --task` does, what
  the default changes, shows one example command, and lists the options
  with the recommended one first

#### Scenario: Every asking skill points to the reference
- **WHEN** a SKILL.md mentions `AskUserQuestion`
- **THEN** it and its harness body contain
  `skills/document/references/question-brief.md`
