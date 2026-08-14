## ADDED Requirements

### Requirement: Evidenced readiness attestation
id: readiness-attestation

Before proceeding from investigation to emission, the `am:plan` skill SHALL
print a user-visible readiness attestation discharging each of the four
checklist items with concrete evidence: items 1–3 (problem and motivation,
bounded scope and non-goals, affected capabilities and files) SHALL each cite
a capability name, a `file:line` reference, or a requirement id, and item 4
SHALL either name every task-shaping decision with how it was settled
(investigation, personal memory, the oracle, or the user) or state explicitly
that none remain. If an item cannot be discharged by such evidence, then the
skill SHALL treat it as unmet and SHALL NOT proceed to emission. Internal
reasoning SHALL NOT substitute for the printed attestation.

#### Scenario: Attestation precedes emission
- **WHEN** investigation satisfies the readiness checklist
- **THEN** the skill prints one cited line per checklist item before authoring
  any artifact

#### Scenario: An uncitable item blocks the auto-proceed
- **WHEN** the affected files cannot be named concretely
- **THEN** the skill treats item 3 as unmet, does not emit, and resolves it by
  investigation or by a question round

#### Scenario: Item four names how each decision was settled
- **WHEN** the oracle settled one decision and the user settled another
- **THEN** the attestation's fourth line names both decisions and their
  settling rung rather than asserting that nothing is open

### Requirement: Gate-promoted hand-off
id: gate-promoted-handoff

After a fresh (non-enrichment) change installs clean, the skill SHALL promote
it by running `spec_gate.py <change> --root <repo-root>` rather than
`spec_status.py set-status ready`. When the gate exits 0 the change is at
`ready` and the skill SHALL hand off with the motivation-led summary. If the
gate exits 2, then the skill SHALL enter its enrichment loop on the findings
the gate wrote into `## Context insufficient` instead of handing off, and
SHALL NOT move the change out of `rejected` with `set-status` or `--force`.

#### Scenario: Fresh plan promotes through the gate
- **WHEN** a freshly emitted change installs clean
- **THEN** the skill runs the context gate, which promotes the change to
  `ready`, and no bare `set-status ready` is issued

#### Scenario: A rejected gate enters enrichment instead of handing off
- **WHEN** the gate exits 2 on a freshly emitted change
- **THEN** the skill works the `## Context insufficient` findings as its
  enrichment agenda rather than reporting the plan as ready

#### Scenario: The gate verdict is never forced
- **WHEN** a gate rejection remains unresolved
- **THEN** the change stays at `rejected` and the skill does not force it to
  `ready`

## MODIFIED Requirements

### Requirement: Investigation findings digest
id: investigation-findings-digest
base: db23564bb355

When investigation completes, the skill SHALL present a short user-visible
findings digest — the affected files and capabilities, the relevant existing
behavior and patterns found, and anything surprising — as plain response text
whose job is situational awareness. The digest SHALL be organized as short
headed groups of concise dot-points, each point about two lines at most,
favoring succinctness over exhaustiveness, and SHALL include a compact diagram
when the findings carry a proposed shape or flow, and always when the user's
request asked for one. The digest SHALL NOT end on a go-ahead question: when
the readiness attestation holds and no un-inferrable task-shaping decision
remains, the skill SHALL continue in the same turn through the depth gate to
emission rather than asking the user for permission to plan. When one or more
un-inferrable task-shaping decisions do remain, the digest SHALL name them
under an `OPEN QUESTIONS` header, the skill SHALL consult the oracle rung on
each in that same turn, and the turn SHALL end on a typed question round for
the `INSUFFICIENT` remainder — so the user is interrupted at most once, and
only for a decision no rung below them could settle. No AskUserQuestion SHALL
be issued in the investigation turn, and internal reasoning SHALL NOT
substitute for the digest.

#### Scenario: Sufficient context proceeds without asking
- **WHEN** investigation leaves no un-inferrable task-shaping decision and the
  readiness attestation holds
- **THEN** the skill emits the artifacts in the same turn as the digest,
  asking the user nothing — no go-ahead question and no proceed prompt

#### Scenario: Remaining decisions reach one typed round in the same turn
- **WHEN** investigation leaves two decisions the oracle returns
  `INSUFFICIENT` for
- **THEN** one message carries the digest, the `OPEN QUESTIONS` header, and
  the numbered typed round, and the turn ends there

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

### Requirement: Readiness checklist gate
id: readiness-checklist-gate
base: 0360349165c3

The skill SHALL emit artifacts only when all of the following hold: the
problem statement is clear and the motivation is stateable in at most two
precise sentences grounded in the request and repository context; scope and
non-goals are bounded; the affected capabilities and files are identified;
and no open decision remains that would change the task list. Each item SHALL
be discharged with concrete evidence and published as the readiness
attestation, never asserted from internal reasoning alone. If the motivation
cannot be stated precisely from the available context, then the skill SHALL
treat it as un-inferrable and obtain it from the user before emission. While
any item is unsatisfied, the skill SHALL keep investigating or ask the user —
never emit a speculative spec.

#### Scenario: Open decision blocks emission
- **WHEN** a decision that would change the task list is still unresolved
- **THEN** the skill does not emit artifacts and instead resolves the
  decision by investigation or a question round

#### Scenario: Ungrounded motivation blocks emission
- **WHEN** the request and repository context do not yield a precise
  motivation for the change
- **THEN** the skill asks the user for the motivation before emitting,
  rather than guessing one

#### Scenario: Each item is discharged with evidence
- **WHEN** the checklist is evaluated
- **THEN** every item carries a citation or a named settled decision in the
  published attestation, and an item with neither counts as unmet

### Requirement: Shared-understanding summary closes the depth path
id: shared-understanding-summary
base: c54085a7d2b8

When the depth gate opens no interactive rounds — the fast path, or a depth
path whose agenda of open decisions is empty — the skill SHALL proceed
directly to emission without presenting a shared-understanding summary or an
emit confirmation. When instead the depth path's grill loop actually runs one
or more rounds, the skill SHALL, when that loop ends, present a
shared-understanding summary — the problem, the chosen approach, each decision
with a one-line rationale, and known risks — and SHALL obtain the user's
confirmation, with `emit` the recommended option, before proceeding to
emission.

#### Scenario: No interactive rounds emits directly
- **WHEN** the depth gate opens no interactive rounds
- **THEN** the skill proceeds directly to emission without presenting a
  shared-understanding summary or an emit confirmation

#### Scenario: An empty depth agenda skips the summary
- **WHEN** the depth gate selects the depth path but every task-shaping
  decision is already settled, so the grill loop asks nothing
- **THEN** the skill emits without the summary or its confirmation

#### Scenario: A grill loop that ran confirms before emitting
- **WHEN** the grill loop runs at least one round and resolves its last open
  decision
- **THEN** the skill presents the shared-understanding summary and waits for
  the user's `emit` confirmation before authoring any artifact

### Requirement: Oracle consultation before user question rounds
id: oracle-consultation
base: 70581761894a

When genuinely un-inferrable task-shaping decisions remain and a user question
round would otherwise open — the investigation turn's round, a depth-path
round, or enrichment's true-gap round — the skill SHALL first shape each
remaining decision into a compact question (the decision, concrete options,
and the skill's recommended default) and consult the `s:oracle` agent with
one spawn per decision, passing the compact question, the asking repo's
absolute root, and the status CLI path. The skill SHALL branch on the
verdict's first non-blank line: a decision answered `ANSWER` SHALL be folded
in as resolved and SHALL NOT be put to the user, while a decision returned
`INSUFFICIENT` SHALL proceed to the user round unchanged. If a spawn fails or
the verdict's first line is neither `ANSWER` nor `INSUFFICIENT`, then the
skill SHALL treat that decision as `INSUFFICIENT` and continue — the
consultation SHALL never block planning. When the findings digest leaves open
task-shaping decisions, the skill SHALL consult the rung in that same turn, so
the digest, the consultation, and the round for the `INSUFFICIENT` remainder
form a single message exchange.

#### Scenario: Wiki-held answers skip the user round
- **WHEN** every remaining un-inferrable decision comes back `ANSWER`
- **THEN** the skill proceeds toward the readiness gate without opening a
  user question round

#### Scenario: Insufficient decisions still go to the user
- **WHEN** the oracle returns `INSUFFICIENT` for a decision
- **THEN** that decision appears in the user question round exactly as it
  would have without the rung

#### Scenario: A failed spawn degrades instead of blocking
- **WHEN** an oracle spawn errors or returns a first line that is neither
  `ANSWER` nor `INSUFFICIENT`
- **THEN** the skill treats that decision as `INSUFFICIENT` and the flow
  continues without error

#### Scenario: The digest's open questions are consulted in that turn
- **WHEN** the findings digest names open task-shaping questions
- **THEN** the oracle is consulted on them before the turn ends, rather than
  deferred to a later turn

### Requirement: Emission carries the status header
id: emission-carries-status-header
base: 46d3df98d411

The plan flow SHALL emit every `plan.md` with the `# <change-name>` title and
`Status: draft` header, and SHALL promote the status to `ready` only through
the context gate, which runs the deterministic context checks on the installed
change and settles its status.

#### Scenario: Fresh emission is draft
- **WHEN** plan emits a change's artifacts
- **THEN** the `plan.md` begins with the title and `Status: draft`

#### Scenario: The gate performs the promotion
- **WHEN** the emitted change installs clean and passes the context gate
- **THEN** the plan's status line reads `Status: ready` before hand-off to
  execution, written by the gate rather than by a bare status set
