# shipd-plan

### Requirement: Convergent plan flow
id: convergent-plan-flow

The `am:plan` skill SHALL run an explore-stance flow whose explicit goal is
reaching spec-readiness and stopping — not open-ended exploration. Once the
readiness checklist is satisfied, the skill SHALL proceed to artifact emission
rather than continuing to explore or ask further questions.

#### Scenario: Plan converges instead of wandering
- **WHEN** the readiness checklist is satisfied mid-conversation
- **THEN** the skill stops investigating, emits the spec artifacts, and ends —
  it does not open new threads of exploration

### Requirement: Codebase-first investigation
id: codebase-first-investigation

Before asking the user anything, the skill SHALL investigate the repository —
existing `am/verified/` capabilities, relevant code, and the user's request —
and SHALL NOT ask the user any question whose answer is discoverable from the
repo or the request.

#### Scenario: Discoverable facts are not asked
- **WHEN** the affected module and its existing patterns are identifiable from
  the codebase
- **THEN** the skill reads them directly and asks the user nothing about them

### Requirement: Batched user questions on the fast path
id: batched-user-questions

While on the fast path, when decisions remain that the skill cannot infer, it
SHALL batch them into a single AskUserQuestion call of two to four focused
questions, each with concrete options and a recommended default listed first,
and SHALL NOT drip questions one at a time across multiple turns. This
batching contract SHALL NOT apply on the depth path, where the grill loop's
grouped-round protocol governs instead.

#### Scenario: Un-inferrable decisions are batched
- **WHEN** the fast path leaves three genuinely open decisions after
  investigation
- **THEN** the skill issues one AskUserQuestion call containing all three, each
  with concrete options and a recommended default first

#### Scenario: No questions when context suffices
- **WHEN** the user's request plus the codebase already satisfy the readiness
  checklist
- **THEN** the skill proceeds to emission without asking the user anything

#### Scenario: Depth path is exempt from batching
- **WHEN** the depth gate has selected the depth path
- **THEN** questions follow the grill loop's grouped-round protocol — not this
  contract's single fixed batch

### Requirement: Readiness checklist gate
id: readiness-checklist-gate

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

### Requirement: Silent lean-artifact emission
id: silent-lean-emission

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope,
capabilities, and impact and whose `## Implementation` section carries the
binding technical decisions; delta specs carrying `id:` slugs and `base:`
hashes; and a separate `tasks.md` — in a staging area, and SHALL install it
through `spec_emit.py change <name> --from <staging>`, never writing into
the spec tree directly or constructing its path. When a constitution
document is present, the emitted artifacts SHALL honor its rules. Emitted
tasks SHALL be small, independently-executable, and name their target files;
each task SHALL carry a `[req: ...]` traceability tag per the tasks format;
and where a task has a testable surface, the task list SHALL sequence the
failing test before the implementation that makes it pass.

#### Scenario: Emission installs through the engine
- **WHEN** the readiness gate passes
- **THEN** the staged artifacts are installed via `spec_emit.py change`,
  and the resolved `planned/<change>/` contains `plan.md` with `## Idea`
  and `## Implementation` sections, at least one delta spec, and a tasks
  checklist

#### Scenario: Rejected emission never lands
- **WHEN** the staged artifacts carry a lint error at install time
- **THEN** `spec_emit.py` reports the findings and the spec tree gains no
  change directory

#### Scenario: Emitted tasks carry traceability tags
- **WHEN** the task list is emitted
- **THEN** every task names the delta requirement(s) it implements via a
  `[req: ...]` tag (or a lone wildcard for whole-change tasks)

### Requirement: Emitted artifacts pass lint
id: emitted-artifacts-pass-lint

After emission, the skill SHALL run `spec_lint.py` on the change and fix any
reported errors before declaring the plan complete, so every plan hands off a
mergeable change.

#### Scenario: Lint gates plan completion
- **WHEN** `spec_lint.py` reports an error in the emitted artifacts
- **THEN** the skill corrects the artifacts and re-lints until the exit status
  is zero before finishing

### Requirement: Standalone invocation
id: standalone-invocation

The skill SHALL be invocable on its own (`/s:plan <request>`), ending after
artifact emission with a hand-off summary and a pointer to build — without
starting any implementation. The hand-off summary SHALL lead with the
change's Motivation (why it is being built), followed by a brief summary of
the Implementation approach, and SHALL NOT enumerate the artifact files
written. The summary SHALL still name the change and where it lives so the
user can act on it.

#### Scenario: Plan without build
- **WHEN** a user invokes `am:plan` directly and the flow completes
- **THEN** the skill summarizes what is being built and stops; no
  implementation work begins

#### Scenario: Summary leads with the why
- **WHEN** the plan flow completes and hands off
- **THEN** the summary opens with the plan's Motivation, follows with the
  Implementation approach, and contains no inventory of the files created

### Requirement: Emission carries the status header
id: emission-carries-status-header

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

### Requirement: Self-review before the lint gate
id: emission-self-review

After authoring the artifacts and before running the linter, the plan flow
SHALL re-read the drafted `plan.md`, delta specs, and `tasks.md` looking for
placeholders, internal contradictions, and decisions left unresolved for the
executor, and SHALL fix what it finds before proceeding to lint. The lint
gate checks structure; this pass checks sense.

#### Scenario: Placeholder is caught before lint
- **WHEN** the drafted artifacts contain a placeholder or a task that would
  force the executor to choose an approach
- **THEN** the plan flow resolves it during self-review, before the linter
  runs

### Requirement: Metadata-aware emission
id: metadata-aware-emission

When the user's request supplies a profile, theme, epic, or initiative for
the change, the plan flow SHALL record it as the corresponding header
metadata line in the emitted `plan.md`, honoring the initiative-through-epic
rule. When the request supplies none, emission SHALL write no metadata lines,
leaving the change at the implied `full` profile.

#### Scenario: Requested lite profile is recorded
- **WHEN** the user asks for a quick, low-ceremony change and the plan flow
  emits it as lite
- **THEN** the emitted `plan.md` header carries `Profile: lite`

#### Scenario: Default emission stays bare
- **WHEN** the request names no profile, theme, epic, or initiative
- **THEN** the emitted header contains only the title and `Status:` line

### Requirement: Depth gate after investigation
id: depth-gate

When investigation completes, the `am:plan` skill SHALL classify the change as
fast-path or depth-path by counting explicit signals — multiple viable
approaches whose choice changes the task list; an outcome-shaped rather than
mechanism-shaped request; a new capability being added; blast radius spanning
multiple capabilities; uncertainty language in the request — selecting the
depth path at two or more signals and the fast path otherwise. If the request
contains an explicit depth override (e.g. "grill me") or fast override (e.g.
"just plan it"), then the skill SHALL honor the override regardless of the
signal count. The skill SHALL announce the selected mode to the user in one
sentence.

#### Scenario: Complex change trips the gate
- **WHEN** investigation surfaces two viable architectures whose choice changes
  the task list and the request describes an outcome rather than a mechanism
- **THEN** the skill announces depth mode and enters the grill loop instead of
  issuing a single batched question call

#### Scenario: Simple change stays on the fast path
- **WHEN** investigation finds one obvious approach for a mechanism-shaped
  request touching one existing capability
- **THEN** the skill proceeds on the fast path with at most one batched
  question call and loads no dialogue reference

#### Scenario: User override beats the signal count
- **WHEN** the request says "just plan it" but the signal count is two or more
- **THEN** the skill takes the fast path

### Requirement: Bounded grill loop on the depth path
id: grill-loop

While on the depth path, the skill SHALL load the dialogue reference, derive
the agenda of open task-shaping decisions, and partition it: decisions whose
framing does not depend on another answer SHALL be grouped into a single
AskUserQuestion call of up to four questions, each with its recommended option
listed first; decisions whose question cannot be phrased until an earlier
answer lands SHALL be asked one at a time in dependency order. When unsure
whether a decision is independent, the skill SHALL treat it as dependent.
Discoverable facts SHALL be read from the repository, never asked. The loop
SHALL end when no open decision would change the task list. If the agenda of
open decisions exceeds roughly six, then the skill SHALL suggest decomposing
the change via `/s:epic` rather than continuing the interview.

#### Scenario: Independent decisions are grouped into one call
- **WHEN** the depth path has three open decisions whose framing does not
  depend on each other's answers
- **THEN** the skill asks all three in a single AskUserQuestion call, each
  with a recommended option first

#### Scenario: Dependent chain is resolved one at a time
- **WHEN** the question for decision B cannot be phrased until decision A is
  answered
- **THEN** the skill asks A first and poses B in a later round shaped by A's
  answer

#### Scenario: Loop terminates at readiness
- **WHEN** the last open decision that would change the task list is resolved
- **THEN** the skill stops asking and proceeds toward emission

#### Scenario: Oversized agenda suggests decomposition
- **WHEN** the agenda of open task-shaping decisions grows past roughly six
- **THEN** the skill suggests `/s:epic` instead of continuing the interview

### Requirement: Visualization on demand
id: visualization-on-demand

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

### Requirement: Shared-understanding summary closes the depth path
id: shared-understanding-summary

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

### Requirement: Context brief before question rounds
id: context-brief

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

### Requirement: Missing-layout guard
id: missing-layout-guard

When the repository lacks the resolved content-directory layout, the skill
SHALL stop before any questioning, report the missing layout, and ask via
one AskUserQuestion whether to scaffold the minimal layout (`verified/`,
`planned/`, `completed/` under the resolved content directory, default
`.shipd/`) and continue, or stop; it SHALL NOT continue planning as though the
layout existed.

#### Scenario: Missing layout stops the flow
- **WHEN** `/s:plan` runs in a repository with no resolved content
  directory
- **THEN** the skill reports the missing layout and asks scaffold-or-stop
  before any planning question is posed

#### Scenario: Accepted scaffold proceeds
- **WHEN** the user accepts the scaffold option
- **THEN** the skill creates the three empty directories under the resolved
  content directory and continues the normal flow

### Requirement: Version announcement
id: version-announcement

When the skill starts, it SHALL read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`am:plan v<version>` in its first user-visible status sentence, so a session
always displays which plugin snapshot it is running and a stale snapshot is
recognizable on sight.

#### Scenario: First status line names the running version
- **WHEN** `/s:plan` starts in any repository
- **THEN** the first user-visible sentence includes `am:plan v<version>` with
  the version read from the running snapshot's `plugin.json`

#### Scenario: Stale snapshot is recognizable
- **WHEN** the plugin cache holds an older snapshot than the repo's
  `plugins/s/` source
- **THEN** the announced version exposes the mismatch to the user

### Requirement: Enrichment mode activation
id: enrichment-mode-activation

When `/s:plan` receives an argument, the skill SHALL run the engine's
`locate` verb on it before any other flow step. When locate reports the change
at status `rejected`, the skill SHALL announce enrichment mode in one sentence
and operate on the located root for the rest of the session, in place of the
fresh-planning flow (no investigation digest, depth gate, or emission). When
locate reports the change at any other status, the skill SHALL report the
change's location and status and stop — it SHALL NOT start a fresh plan under
a colliding name. When locate finds no match, the skill SHALL proceed with the
normal planning flow unchanged.

#### Scenario: Rejected change enters enrichment
- **GIVEN** a member change parked at `rejected` in its worktree
- **WHEN** `/s:plan <change>` runs from the main checkout
- **THEN** the skill announces enrichment mode and works on the located
  worktree's change instead of planning afresh

#### Scenario: Non-rejected existing change is reported, not re-planned
- **WHEN** `/s:plan <change>` locates the change at `active`
- **THEN** the skill reports the location and status and stops without
  planning or editing anything

#### Scenario: Unlocated argument plans normally
- **WHEN** `/s:plan <request>` finds no installed change matching the
  argument
- **THEN** the normal investigate-then-emit flow runs unchanged

### Requirement: Enrichment gap diagnosis
id: enrichment-gap-diagnosis

While in enrichment mode, the skill SHALL read the change's artifacts through
the engine's `cat change` verb and treat the plan's `## Context insufficient`
findings as the work agenda. It SHALL resolve every codebase-answerable
finding directly by editing the installed artifacts in the located change
directory — refreshing stale `base:` hashes against the current master
requirement and reconciling the delta, correcting dangling task file
references, and replacing placeholder markers with decisions grounded in the
repository — and SHALL put to the user only findings the repository cannot
answer, batched under the fast-path typed-round contract with a context brief.
The skill SHALL NOT ask about anything discoverable from the repository.

#### Scenario: Stale hash is refreshed without asking
- **GIVEN** a rejected plan whose finding names a stale `base:` hash
- **WHEN** enrichment runs
- **THEN** the skill re-reads the master requirement, updates the delta's
  base hash and content, and asks the user nothing about it

#### Scenario: True gap goes to the user
- **GIVEN** a finding naming a placeholder that encodes an undecided
  product choice the repository cannot answer
- **WHEN** enrichment reaches it
- **THEN** the skill asks the user in a typed round preceded by a context
  brief, and folds the answer into the artifacts

### Requirement: Enrichment exits through the re-gate
id: enrichment-regate

When the enrichment agenda is resolved, the skill SHALL re-run the gate engine
(`spec_gate.py <change>`) on the located root. On exit 0 the skill SHALL
confirm the change now sits at `ready` and hand off with the motivation-led
summary. On exit 2 the skill SHALL present the remaining findings and continue
enrichment with them as the new agenda. The skill SHALL NOT move an enrichment
change out of `rejected` via `set-status` or `--force` — the gate's verdict is
the only exit to `ready`.

#### Scenario: Passing re-gate hands off ready
- **WHEN** the re-gate exits 0 on an enriched change
- **THEN** the change's status reads `ready`, the findings section is gone,
  and the skill hands off with the motivation-led summary

#### Scenario: Failing re-gate continues enrichment
- **WHEN** the re-gate exits 2 with one remaining finding
- **THEN** the skill presents that finding and keeps enriching rather than
  ending or forcing the status

### Requirement: Oracle consultation before user question rounds
id: oracle-consultation

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

### Requirement: Oracle-settled decisions stay visible
id: oracle-resolution-visibility

When the oracle settles one or more decisions, the skill SHALL report each
settled decision in user-visible text as its `Q<n>` ledger reference with a
one-line summary of the question and a one-line summary of the answer,
together with who settled it and its `Cited:` source(s) — in the round's
context brief when a round still opens for the remaining decisions, or in the
status text before proceeding when nothing remains to ask. The report SHALL
name `/s:teach <change> Q<n>` as the path for correcting a settled answer. If
the user's typed reply contradicts an oracle-settled decision, then the user's
choice SHALL govern.

#### Scenario: Partially settled agenda is reported in the brief
- **WHEN** the oracle answers some decisions and a round opens for the rest
- **THEN** the context brief lists each oracle-settled decision as
  `Q<n> — <question summary> → <answer summary>` with its citations before
  the numbered questions

#### Scenario: Fully settled agenda is reported before proceeding
- **WHEN** the oracle answers every remaining decision and no round opens
- **THEN** the skill states each settled decision's `Q<n>` reference,
  question and answer summaries, and citations in visible status text before
  moving to the readiness gate

#### Scenario: The correction path is named
- **WHEN** any oracle-settled decision is reported
- **THEN** the report points at `/s:teach <change> Q<n>` for teaching the
  oracle a different answer

#### Scenario: User override beats the oracle
- **WHEN** the user's typed reply contradicts a decision the oracle settled
- **THEN** the plan follows the user's choice, not the oracle's answer

### Requirement: Personal memory consultation during investigation
id: memory-consultation

During investigation and before any user question round, the `am:plan` skill
SHALL read the personal memory store directly — resolving it with
`spec_status.py wiki-show --personal` and reading its catalogue with `cat wiki
index --personal` — and SHALL perform this as a direct store read that spawns no
`s:oracle` agent, so the investigation turn stays oracle-free. Where the
personal store is absent or holds no page relevant to the change, the skill
SHALL skip the consultation silently and SHALL NOT block planning. Where one or
more relevant `memory-*` pages exist — matched by index and read-only grep over
the change's subject terms — the skill SHALL read each and apply it to its plan
decisions and to its output and expression (including diagram style and tone),
and SHALL report each applied memory in user-visible text with its source slug.
If the user's typed reply contradicts an applied memory, then the user's choice
SHALL govern.

#### Scenario: Relevant memory shapes the plan and is reported
- **WHEN** a captured `memory-*` page is relevant to the change under
  investigation
- **THEN** the skill reads it, applies it to a plan decision or the plan's
  output, and reports it in user-visible text with its source slug

#### Scenario: Output-style preference applies with no open decision
- **WHEN** a relevant memory expresses an output/style preference (e.g. ASCII
  diagrams) and no un-inferrable decision would open a user question round
- **THEN** the skill still applies the preference to the plan's output, even
  though the oracle rung never fires

#### Scenario: Absent store is skipped silently
- **WHEN** no personal store exists, or none of its pages is relevant to the
  change
- **THEN** the skill skips the consultation without error and planning proceeds
  unchanged

#### Scenario: User override beats an applied memory
- **WHEN** the user's typed reply contradicts a memory the skill applied
- **THEN** the plan follows the user's choice, not the memory

#### Scenario: The consultation keeps the investigation turn oracle-free
- **WHEN** the skill consults personal memories during investigation
- **THEN** it does so by a direct store read and spawns no `s:oracle` agent in
  that turn

### Requirement: Evidenced readiness attestation
id: readiness-attestation

Before proceeding from investigation to emission, the `am:plan` skill SHALL
print the user-visible readiness attestation as a markdown table with one
cited row per checklist item, each row carrying the item's name and its
concrete evidence: the rows for items 1–3 (problem and motivation, bounded
scope and non-goals, affected capabilities and files) SHALL each cite a
capability name, a `file:line` reference, or a requirement id, and item 4's
row SHALL either name every task-shaping decision with how it was settled
(investigation, personal memory, the oracle, or the user) or state explicitly
that none remain. If an item cannot be discharged by such evidence, then the
skill SHALL treat it as unmet and SHALL NOT proceed to emission. Internal
reasoning SHALL NOT substitute for the printed attestation.

#### Scenario: Attestation precedes emission
- **WHEN** investigation satisfies the readiness checklist
- **THEN** the skill prints a markdown table with one cited row per checklist
  item before authoring any artifact

#### Scenario: An uncitable item blocks the auto-proceed
- **WHEN** the affected files cannot be named concretely
- **THEN** the skill treats item 3 as unmet, does not emit, and resolves it by
  investigation or by a question round

#### Scenario: Item four names how each decision was settled
- **WHEN** the oracle settled one decision and the user settled another
- **THEN** the attestation's fourth row names both decisions and their
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

### Requirement: Video entry point
id: plan-video-entry

Where `/s:plan`'s argument names a recording — a path whose extension is a
recognized video container — or a slug that resolves to an existing ingest
bundle, the skill SHALL obtain a video intent brief before investigating, by
invoking the `/s:video-ingest` skill **by reference** rather than
reimplementing ingestion, passing the recording path or the bundle slug
through unchanged. The resulting brief SHALL be used as an **input to**
investigation, and the codebase-first investigation SHALL still run — the brief
establishes what the speaker wants, the repository still establishes which
capability owns it. Where the brief carries a `Project:` line **and** the
planning repository resolves to a declared project in the workspace registry,
the skill SHALL compare the two and, on a mismatch, report both project names
and stop without emitting a change, unless the invocation carries an explicit
`--cross-project` override, in which case it SHALL proceed and say so. Where
either side is absent there is nothing to compare and the skill SHALL proceed
without a project check. Where the argument is neither a recording nor a bundle
slug, the skill SHALL fall through to its ordinary flow unchanged. The skill
SHALL name the installed brief in user-visible text so its provenance is
traceable.

#### Scenario: A recording is ingested before investigation
- **WHEN** `/s:plan` is invoked with a path to a video container
- **THEN** a brief is obtained through the `/s:video-ingest` skill and the
  codebase-first investigation still runs afterwards

#### Scenario: An existing bundle is reused rather than re-ingested
- **WHEN** the argument is a slug resolving to an existing bundle
- **THEN** that bundle's brief is used without re-ingesting the recording

#### Scenario: A foreign project stops the plan
- **WHEN** the brief carries a `Project:` naming a different declared project
  than the planning repository resolves to
- **THEN** the skill reports both project names and ends the turn without
  emitting a change

#### Scenario: The override proceeds deliberately
- **WHEN** the same mismatch occurs and the invocation carries
  `--cross-project`
- **THEN** the skill proceeds through its ordinary flow and states in
  user-visible text that the project check was overridden

#### Scenario: An unresolvable project side skips the check
- **WHEN** the brief carries no `Project:` line, or the planning repository
  resolves to no declared project
- **THEN** no project comparison is attempted and planning proceeds

#### Scenario: An ordinary argument is unaffected
- **WHEN** the argument is neither a recognized video path nor a resolvable
  bundle slug
- **THEN** the skill runs its ordinary flow with no ingest attempted

#### Scenario: The brief does not replace reading the repository
- **WHEN** planning proceeds from a brief
- **THEN** the affected capabilities and files are still established by reading
  the repository, not taken from the brief alone

### Requirement: Epic-sized briefs are reported, not emitted
id: plan-video-epic-advisory

Where a brief's intents are too broad to be served by a single change, `/s:plan`
SHALL report that the brief reads as epic-sized, name the intents that drove
that read, recommend `/s:epic`, and stop **without emitting a change**. The
skill SHALL NOT invoke `/s:epic` itself, and SHALL NOT apply a mechanical
threshold — the assessment is a judgement the skill states and the user
settles. Where the brief's intents are within one change's scope, the skill
SHALL proceed to emission as usual.

#### Scenario: A broad brief stops before emission
- **WHEN** a brief's intents are too broad for one change
- **THEN** the skill reports that assessment with the intents behind it,
  recommends `/s:epic`, and installs no change

#### Scenario: The user decides, not the skill
- **WHEN** the skill judges a brief epic-sized
- **THEN** it does not invoke `/s:epic` and leaves the decision to the user

#### Scenario: A focused brief proceeds normally
- **WHEN** a brief's intents fit within a single change
- **THEN** the skill continues through the depth gate to emission without
  raising the epic recommendation

### Requirement: Runnable premises are verified before emission
id: verified-runnable-premises

Where a plan asserts how an **existing** command, script, or flag behaves, and a
task or delta requirement depends on that assertion, the planner SHALL verify it
by running that command before emitting, and SHALL cite what was observed — the
invocation and its output or exit code — rather than a pointer to the
implementation's source. Assertions about behavior the change itself will create,
and assertions no task depends on, SHALL NOT require verification.

#### Scenario: A relied-on claim about an existing command is run
- **GIVEN** a plan whose task list depends on an existing script exiting zero on
  a second invocation
- **WHEN** the planner reaches emission
- **THEN** that script has been run and the plan cites the invocation and the
  observed exit code

#### Scenario: Reading the source is not verification
- **GIVEN** a plan asserting an existing command's behavior, supported only by a
  citation of that command's implementation
- **WHEN** the readiness attestation is checked
- **THEN** the premise counts as unverified

#### Scenario: Claims about not-yet-written behavior are exempt
- **GIVEN** a plan describing how the component this change will create should
  behave
- **WHEN** the planner reaches emission
- **THEN** no verification run is required for that description

#### Scenario: A premise no task depends on is exempt
- **GIVEN** a plan mentioning an existing command's behavior in passing, with no
  task or delta requirement depending on it
- **WHEN** the planner reaches emission
- **THEN** no verification run is required for that mention

### Requirement: Premise evidence appears in the readiness attestation
id: premise-evidence-in-attestation

The readiness checklist SHALL carry the runnable-premise rule as evidence under
its affected-capabilities-and-files item rather than as an additional checklist
item, so the four items are unchanged in number. The attestation SHALL name each
verified premise with its observation.

#### Scenario: The checklist keeps four items
- **WHEN** the readiness checklist is read after this change
- **THEN** it still gates on exactly four items

#### Scenario: The attestation carries the observation
- **GIVEN** a plan that verified a runnable premise
- **WHEN** its readiness attestation is printed
- **THEN** the attestation names the premise and what running it showed

### Requirement: Questions-and-answers ledger in the emitted plan
id: plan-qa-ledger

When at least one oracle consultation ran while planning a change, the emitted
`plan.md` SHALL carry a `## Questions and answers` section recording every
consultation of that planning session as a `### Q<n>: <one-line question
summary>` entry, numbered sequentially from `Q1` in consultation order. Each
entry SHALL carry the full compact question (decision, options,
recommendation), the verdict (`ANSWER` or `INSUFFICIENT`), an
`Answered by:` property holding `ORACLE` or `USER` placed directly above the
answer, and the answer in full — the oracle's position for `ANSWER`, the
user's typed resolution for `INSUFFICIENT`; an `ANSWER` entry SHALL carry the
oracle's `Cited:` sources and an `INSUFFICIENT` entry SHALL carry the
`Queued:` `q-<slug>` the oracle filed. Entries SHALL be phrased to avoid the context
gate's placeholder and open-question marker scans. When enrichment consults the
oracle on an installed change, the skill SHALL append the new consultations to
the existing section, continuing the numbering. When no consultation ran, the
skill SHALL emit no such section.

#### Scenario: Oracle-settled consultation is recorded
- **WHEN** the oracle answers `ANSWER` on a decision during planning
- **THEN** the emitted `plan.md` holds a `### Q<n>:` entry carrying the
  compact question, the verdict, `Answered by: ORACLE` above the answer, the
  oracle's position, and its `Cited:` sources

#### Scenario: User-settled consultation is recorded with its queue link
- **WHEN** the oracle returns `INSUFFICIENT` and the user's typed reply
  settles the decision
- **THEN** the entry records the compact question, `Answered by: USER` above
  the answer, the user's resolution, and the `Queued: q-<slug>` the oracle
  filed

#### Scenario: No consultations, no section
- **WHEN** planning completes without any oracle consultation
- **THEN** the emitted `plan.md` carries no `## Questions and answers` section

### Requirement: Plan-side pipeline resolution
id: plan-pipeline-resolution

When the plan flow starts, it SHALL resolve the effective autonomous
pipeline by running the status CLI's `pipeline-show --json` verb, reading
the provenance from the emitted object's `source` field rather than
parsing the human-rendered header line. If the
resolution exits non-zero (a validation error or missing pydantic), then
the flow SHALL report the engine's error text and stop before
investigation or any question round — a declared pipeline never
half-runs. Where a configuration layer declares the pipeline (list or
preset) — a `source` other than `default` — the flow SHALL name the
resolved provenance in its first
user-visible status text alongside the version announcement; a default
pipeline (`source` `default`) SHALL add no announcement. The flow
SHALL ignore the plan entry's `model` option and every `autopilot` block
— interactively the session's model is the user's choice and the human
is the retry loop — and SHALL run its ending's context-gate promotion
unchanged regardless of the pipeline's gate entry: a gate `skip` or
`autopilot.attempts` value SHALL neither bypass the gate nor permit a
forced status.

#### Scenario: Malformed pipeline stops planning
- **GIVEN** a declared pipeline entry carrying a misspelled option key
- **WHEN** `/s:plan` starts
- **THEN** the flow reports the resolution error naming the entry and
  field and stops without investigating or emitting

#### Scenario: Declared provenance is announced from the JSON source
- **GIVEN** a repo whose config declares `{"autonomous-pipeline": "eco"}`
- **WHEN** `/s:plan` starts
- **THEN** the first status text names the `preset:eco` provenance with
  its supplying config path, taken from the `--json` object's `source`
  field, alongside the version announcement

#### Scenario: Gate skip never skips the internal gate
- **GIVEN** a resolved pipeline whose gate entry is skipped
- **WHEN** a planned change reaches the plan flow's ending
- **THEN** the context gate still runs and its verdict remains the only
  path to `ready`

#### Scenario: Default pipeline changes nothing
- **GIVEN** no configuration layer declares `autonomous-pipeline`
- **WHEN** `/s:plan` starts
- **THEN** no pipeline provenance is announced and the flow proceeds
  exactly as before
