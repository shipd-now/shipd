## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: 7d0dc3434fda

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
exists, the digest SHALL instead end on a single typed go-ahead prompt —
a plain-text numbered prompt asking whether the findings and proposed
shape are clear enough to proceed, with options exactly: proceed to the
depth gate and planning (recommended, named first), or adjust scope first —
collected from the user's typed reply. No AskUserQuestion SHALL be issued
in the investigation turn, neither ending SHALL contain any planning
decision, and no depth-gate verdict SHALL appear in the investigation
turn. Internal reasoning SHALL NOT substitute for the digest.

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
  proceed/adjust block, and the turn ends there

#### Scenario: No open questions ends the turn on the go-ahead prompt
- **WHEN** investigation leaves no genuinely open task-shaping question
- **THEN** the digest ends on the numbered go-ahead prompt (proceed
  recommended, named first; adjust scope as the alternative) with no
  `OPEN QUESTIONS` header and no AskUserQuestion

### Requirement: Visualization on demand
id: visualization-on-demand
base: 535763740326

Where a diagram or comparison table would clarify a decision being put to
the user, the skill SHALL load the visualization reference (at most once
per session) and attach the visual to the question — as an ASCII diagram,
an options table, or an AskUserQuestion option preview. In question rounds
the skill SHALL NOT emit visuals that do not carry a decision. In the
findings digest the bar is lean-toward: findings that carry a shape or
flow satisfy the carries-a-decision bar by themselves, because the
go-ahead is a decision the user makes by judging that shape. When the
user's request explicitly asks for a diagram or visual, the skill SHALL
honor it, presenting the requested solution diagram no later than the
first context brief (or in the findings digest when no question round
occurs).

#### Scenario: Diagram accompanies an architectural choice
- **WHEN** a depth-path question puts two candidate architectures to the
  user
- **THEN** the question carries a visual comparison of the candidates

#### Scenario: No decorative diagrams in question rounds
- **WHEN** a decision is clear from one sentence of prose and the user
  asked for no visual
- **THEN** the skill asks it without loading the visualization reference

#### Scenario: Digest shape earns a diagram without a request
- **WHEN** investigation findings carry a multi-component proposed shape
  and the user asked for no visual
- **THEN** the digest still includes a compact diagram of the shape

#### Scenario: Explicit diagram request is honored
- **WHEN** the user's request says to draw a diagram of the potential
  solution
- **THEN** a solution diagram appears no later than the first context
  brief, regardless of whether any pending decision needs a visual
