## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: 6dd507e89747

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising — as plain response
text whose job is situational awareness: the user understands where the
flow stands and can ask to dive deeper. The digest SHALL be organized as
short headed groups of concise dot-points, each point about two lines at
most, favoring succinctness over exhaustiveness. When the findings carry a
proposed shape or flow that a compact diagram conveys faster than prose,
the digest SHALL include such a diagram, and it SHALL always include one
when the user's request asked for a diagram. The investigation turn SHALL
end in exactly one of two mutually exclusive ways. When investigation
leaves one or more genuinely open task-shaping questions, the digest SHALL
end on an `OPEN QUESTIONS` header listing them — with no go-ahead prompt
and no clear-enough-to-proceed phrasing; the questions are displayed, not
asked, and the user's next typed message is folded in, with any remaining
questions settled in the post-gate decision rounds. When no such question
exists, the digest SHALL instead end on a single plain-text go-ahead
question — "Shall we proceed with the plan?" — carrying no numbered options
and no AskUserQuestion. That question SHALL drive a loop: an affirmative
reply advances to the depth gate; any other reply (further questions, new
information, or scope changes) SHALL be folded in as continued planning —
the skill keeps planning, shows a one-line delta of what changed, and
re-asks "Shall we proceed with the plan?" once the plan is settled again —
looping until the user affirms. An explicit go-ahead already present in the
user's reply (for example, a bare go-ahead answering an `OPEN QUESTIONS`
list) SHALL count as the affirmative and skip a redundant re-ask. No
AskUserQuestion SHALL be issued in the investigation turn, neither ending
SHALL contain any planning decision, and no depth-gate verdict SHALL appear
in the investigation turn. Internal reasoning SHALL NOT substitute for the
digest.

#### Scenario: Digest renders as grouped dot-points
- **WHEN** investigation completes on a change with several findings
- **THEN** the digest presents them as short headed groups of dot-points
  rather than paragraph-length bullets

#### Scenario: A shaped proposal carries a diagram
- **WHEN** the digest's proposed shape involves components, a flow, or a
  before/after restructuring
- **THEN** the digest includes a compact diagram of that shape

#### Scenario: Shapeless changes need no diagram
- **WHEN** the findings amount to a single-file tweak with no structural
  shape and the user asked for no visual
- **THEN** the digest may omit a diagram without violating the contract

#### Scenario: Open questions end the turn without a go-ahead prompt
- **WHEN** investigation leaves a task-shaping question only the user can
  settle
- **THEN** the digest ends on the `OPEN QUESTIONS` list with no
  proceed prompt, and the turn ends there

#### Scenario: No open questions ends the turn on the proceed question
- **WHEN** investigation leaves no genuinely open task-shaping question
- **THEN** the digest ends on the single plain-text question "Shall we
  proceed with the plan?" with no numbered options, no `OPEN QUESTIONS`
  header, and no AskUserQuestion

#### Scenario: A non-affirmative reply keeps planning and re-asks
- **WHEN** the user answers "Shall we proceed with the plan?" with further
  questions, new information, or a scope change rather than an affirmative
- **THEN** the skill folds the reply in as continued planning, shows a
  one-line delta of what changed, and re-asks "Shall we proceed with the
  plan?" once the plan is settled again, without firing the depth gate

#### Scenario: An in-line go-ahead skips a redundant re-ask
- **WHEN** the user's reply to an `OPEN QUESTIONS` list carries an explicit
  go-ahead
- **THEN** the skill treats it as the affirmative and advances to the depth
  gate without re-asking "Shall we proceed with the plan?"

### Requirement: Shared-understanding summary closes the depth path
id: shared-understanding-summary
base: 70d346cbd2c6

The affirmative to "Shall we proceed with the plan?" SHALL be the sole
approval for a clean gate: when the user affirms and the depth gate opens no
further interactive rounds (the fast path — the gate needs no more info), the
skill SHALL proceed directly to emission without presenting a shared-
understanding summary or an "emit" confirmation. When instead the depth gate
needs more info and the grill loop runs (the depth path), the skill SHALL,
when that loop ends, present a shared-understanding summary — the problem, the
chosen approach, each decision with a one-line rationale, and known risks —
and SHALL obtain the user's confirmation, with "emit" the recommended option,
before proceeding to emission. The fast path SHALL NOT add this step.

#### Scenario: Clean gate emits on the affirmative alone
- **WHEN** the user affirms "Shall we proceed with the plan?" and the depth
  gate opens no interactive rounds
- **THEN** the skill proceeds directly to emission without presenting a
  shared-understanding summary or an "emit" confirmation

#### Scenario: Depth path confirms before emitting
- **WHEN** the depth gate needs more info and the grill loop resolves its
  last open decision
- **THEN** the skill presents the shared-understanding summary and waits for
  the user's "emit" confirmation before authoring any artifact
