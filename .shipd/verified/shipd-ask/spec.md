# shipd-ask

### Requirement: Cited opinionated answers
id: oracle-cited-answers

Where the personal memory store, the wiki, or the asking repo's spec surfaces
hold the answer, the oracle SHALL return `ANSWER` with a single recommended
position (never an uncommitted list of alternatives) and SHALL name the wiki
page(s) or repo artifact(s) behind it on `Cited:` line(s). Every `ANSWER`
SHALL additionally carry at least one `Evidence:` line quoting a cited source
verbatim, so the caller can check that the source states a position on the
specific decision rather than merely touching its topic. Where the position's
source carries an advisory marker — a queue block whose `Answer:` value
begins `advisory: `, or a wiki page carrying an `Authority: advisory` line —
the `ANSWER` SHALL carry an `Authority: advisory` line after its position, so
callers surface it as a recommendation rather than a settlement; an `ANSWER`
with no such line is binding, as before. A citation of a
personal-store wiki page SHALL carry a personal marker — `Cited: [[slug]]
(personal)` — a citation of a page read from an inherited chain store SHALL
carry an inherited marker naming that store's workspace root — `Cited:
[[slug]] (inherited <ws-root>)` — a citation of a base-store wiki page SHALL
carry a base marker — `Cited: [[slug]] (base)` — and a citation of an
answered-but-undrained queue block SHALL read `Cited: queue q-<slug>` — so the
caller can tell which store answered.

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

#### Scenario: Answer carries verbatim evidence
- **WHEN** the oracle returns `ANSWER`
- **THEN** at least one `Evidence:` line quotes a cited source verbatim

#### Scenario: Advisory source yields an advisory answer
- **WHEN** the oracle's answer rests on a queue block whose `Answer:` value
  begins `advisory: ` or a wiki page carrying `Authority: advisory`
- **THEN** the `ANSWER` carries an `Authority: advisory` line after its
  position

#### Scenario: Binding sources carry no authority line
- **WHEN** the oracle's answer rests only on sources without an advisory
  marker
- **THEN** the `ANSWER` carries no `Authority:` line and is treated as
  binding

#### Scenario: Personal-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the personal memory
  store
- **THEN** the citation reads `Cited: [[slug]] (personal)`

#### Scenario: Inherited-store answer is marked
- **WHEN** the oracle's answer rests on a page read from an enclosing
  workspace's store rather than the nearest one
- **THEN** the citation reads `Cited: [[slug]] (inherited <ws-root>)`

#### Scenario: Base-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the base store
- **THEN** the citation reads `Cited: [[slug]] (base)`

#### Scenario: Queue-backed answer is marked
- **WHEN** the oracle's answer rests on an answered-but-undrained queue block
- **THEN** the citation reads `Cited: queue q-<slug>`

### Requirement: Insufficient queues the question
id: oracle-insufficient-queue

If neither the wiki nor the asking repo's spec surfaces answer the question,
then the oracle SHALL return `INSUFFICIENT` with the compact question block
and SHALL append the question to the wiki queue via
`spec_status.py wiki-queue-add` with an `--origin` naming the asking repo,
reporting the slug on a `Queued: q-<slug>` line. The queue write — and any
`wiki-init` scaffolding — SHALL target the asking workspace's own store,
never the base store, which is read-only to the oracle. Before queueing, the
oracle SHALL read the existing queue and cite an equivalent pending question
instead of duplicating it. If the resolved store does not exist yet, then the
oracle SHALL scaffold it with `wiki-init` before queueing. Where no workspace
is discoverable but the asking repo's resolved content directory exists, the
queue write SHALL land in the repo-local fallback store through the same
verbs, which resolve and scaffold it on demand. Only where the asking repo
has neither a discoverable workspace nor a content directory SHALL the
oracle still return its verdict and report `Queued: none` naming the missing
prerequisites instead of failing.

#### Scenario: Unanswerable question is queued
- **WHEN** the oracle cannot answer from the wiki or repo surfaces in a
  workspace with a wiki store
- **THEN** it returns `INSUFFICIENT` and `queue.md` gains a `## q-<slug>`
  block with the question, options, recommendation, and `Answer: pending`

#### Scenario: Queue lands in the job store, not the base
- **GIVEN** a workspace whose `wiki-show` reports a present base store
- **WHEN** the oracle queues an unanswerable question
- **THEN** the block lands in the job store's `queue.md` and the base store
  is unmodified

#### Scenario: Missing store is scaffolded, not fatal
- **WHEN** the oracle must queue a question in a workspace with no wiki store
- **THEN** it runs `wiki-init` and then queues, and the verdict reports the
  `q-<slug>`

#### Scenario: Bare repo queues into the fallback store
- **GIVEN** an asking repo with a content directory and no discoverable
  workspace
- **WHEN** the oracle cannot answer the question
- **THEN** the block lands in `<root>/<content-dir>/wiki/queue.md` and the
  verdict reports `Queued: q-<slug>`, not `Queued: none`

#### Scenario: Uninitialized repo still yields a verdict
- **WHEN** the oracle runs for an asking repo with no discoverable workspace
  and no content directory
- **THEN** it answers from what it can reach or returns `INSUFFICIENT` with
  `Queued: none` naming the missing prerequisites, and does not exit in
  error

### Requirement: Ask skill entry
id: ask-skill

The plugin SHALL provide `/s:ask` at `plugins/s/skills/ask/SKILL.md`: it
SHALL announce the running plugin version, shape the user's request into a
compact question without an interview round, consult the oracle inline per
the oracle consultation contract — running `oracle-lookup` and judging its
output itself, spawning no agent — and relay the verdict. If the verdict's
first line is `ANSWER` but its body lacks a `Cited:` line or an `Evidence:`
line, then the skill SHALL treat the verdict as `INSUFFICIENT`. Where an
`ANSWER` carries an `Authority: advisory` line, the skill SHALL relay it as
a recommendation rather than a settlement: it SHALL still put the decision
to the user with the advisory position as the recommended first option,
naming its citation. When the verdict is `INSUFFICIENT`, the skill SHALL
queue the question per the insufficient-queue rules, then put the compact
question to the user through a single AskUserQuestion dialog with the
recommendation listed first, distill the user's reply into a concise durable
answer, and classify that answer against the capture rubric
(`plugins/s/skills/ask/references/capture-rubric.md`) before any queue
write: an include-tier answer is written through
`spec_status.py wiki-queue-answer` against the filed `q-<slug>`; an
exclude-tier answer discards the block through
`spec_status.py wiki-queue-discard` with a one-line reason; a
consent-gated-tier answer is captured with `wiki-queue-answer --advisory`
only when the user expressly affirms an explicit record-this question, and
is otherwise discarded. Where the verdict reported `Queued: none`, the skill
SHALL relay the answer for the session only and state that nothing durable
was captured. A failed capture or discard write SHALL be reported and SHALL
never block the reply.

#### Scenario: Skill consults the oracle inline
- **WHEN** `plugins/s/skills/ask/SKILL.md` is inspected
- **THEN** it directs shaping a compact question, running `oracle-lookup`
  per the contract reference, relaying `ANSWER` citations, and demoting an
  `ANSWER` missing `Cited:` or `Evidence:` to `INSUFFICIENT`, and it names
  no `s:oracle` agent

#### Scenario: Advisory answer recommends instead of settling
- **WHEN** the SKILL.md's handling of an `ANSWER` carrying
  `Authority: advisory` is inspected
- **THEN** it directs putting the decision to the user with the advisory
  position as the recommended first option, cited, rather than relaying it
  as settled

#### Scenario: Insufficient verdict queues, then defers to the user
- **WHEN** the SKILL.md's `INSUFFICIENT` branch is inspected
- **THEN** it directs queueing through `wiki-queue-add` and then a single
  AskUserQuestion dialog carrying the compact question's options with the
  recommendation first

#### Scenario: Include-tier answer is captured
- **WHEN** the SKILL.md's capture step is inspected
- **THEN** it directs classifying the distilled reply against the capture
  rubric and writing an include-tier answer via `wiki-queue-answer` against
  the filed `q-<slug>`

#### Scenario: Exclude-tier answer discards the block
- **WHEN** the capture step classifies the reply exclude-tier
- **THEN** the SKILL.md directs discarding the filed block via
  `wiki-queue-discard` with a reason instead of capturing

#### Scenario: Consent-gated capture requires express instruction
- **WHEN** the capture step classifies the reply consent-gated
- **THEN** the SKILL.md directs asking an explicit record-this question and
  capturing with `--advisory` only on an express affirmative, discarding
  otherwise

#### Scenario: No workspace relays without capture
- **WHEN** the SKILL.md's `Queued: none` handling is inspected
- **THEN** it directs relaying the answer for the session only and stating
  that nothing durable was captured

### Requirement: Compact question contract
id: compact-question-contract

Every question put to the oracle — and every question the oracle queues —
SHALL be one decision-ready unit carrying the decision, concrete options, and
the asker's recommendation, never a raw trace or an open-ended essay prompt.
Both `plugins/s/skills/ask/references/oracle-contract.md` and
`plugins/s/skills/ask/SKILL.md` SHALL state this contract.

#### Scenario: Both surfaces carry the contract
- **WHEN** the oracle contract reference and the ask SKILL.md are inspected
- **THEN** each states the decision/options/recommendation compact-question
  shape

### Requirement: Oracle user documentation
id: oracle-user-docs

The repository SHALL provide `docs/oracle.md`, a user-facing guide to the
oracle that includes a diagram of the read → oracle → human ladder with the
answer-capture loop, the two verdicts each shown with an example
(`ANSWER` with `Cited:` and `Evidence:` lines; `INSUFFICIENT` with its queued
question), the definitive-evidence answering bar, and the correction path via
`/s:teach`. The guide SHALL additionally document the advisory variant of
`ANSWER` — an `Authority: advisory` line after the position, shown in an
example — stating that an advisory answer is surfaced as a recommended,
citable default the user can accept or override, never a silent settlement,
and that an `ANSWER` without the line is binding. The guide SHALL also
document the classified capture loop: a typed answer is classified against
the capture durability rubric before any queue write — include-tier answers
captured via `wiki-queue-answer`, exclude-tier answers discarding their
pending block via `wiki-queue-discard` with nothing stored, and
consent-gated answers recorded as advisory only on the user's express
record-this instruction. The ladder diagram SHALL be a `mermaid` code fence —
not ASCII box-drawing art — so the published docs site renders it natively,
and its capture path SHALL reflect the classification rather than an
unconditional write. The guide SHALL conform to the shipd documentation
standard: `<!-- doc-type: reference -->` as its first line and a total line
count within the reference cap.

#### Scenario: Guide covers the loop
- **WHEN** `docs/oracle.md` is inspected
- **THEN** it holds a ladder-and-capture-loop diagram, an `ANSWER` example
  with `Cited:` and `Evidence:` lines, an `INSUFFICIENT` example, and names
  `/s:teach` as the correction path

#### Scenario: Guide covers the advisory variant
- **WHEN** `docs/oracle.md` is inspected
- **THEN** it shows an `ANSWER` example carrying an `Authority: advisory`
  line and states that advisory answers are recommended-not-forced while an
  `ANSWER` without the line is binding

#### Scenario: Guide covers classified capture
- **WHEN** the guide's capture-loop description is inspected
- **THEN** it names the three capture tiers, the express-instruction rule
  for consent-gated recording, and `wiki-queue-discard` as the fate of an
  excluded answer's pending block

#### Scenario: Ladder diagram is mermaid
- **WHEN** the ladder diagram in `docs/oracle.md` is inspected
- **THEN** it is a `mermaid` code fence containing the three rungs (read,
  oracle, human), the `ANSWER` and `INSUFFICIENT` verdict branches, and the
  classified capture loop back to the oracle rung, and `docs/oracle.md`
  contains no box-drawing characters

#### Scenario: Guide carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/oracle.md`
- **THEN** it exits 0 with the file marked `reference`

### Requirement: Capture durability rubric
id: capture-rubric

The plugin SHALL provide a capture durability rubric reference at
`plugins/s/skills/ask/references/capture-rubric.md` defining three tiers for
classifying a user's typed answer before any queue capture: **include**
(durable engineering positions — captured immediately as binding knowledge),
**exclude** (self-evidencing or explicitly one-off answers — the pending
queue block is discarded via `wiki-queue-discard`), and **consent-gated**
(workflow workarounds, process habits, and personal preferences — captured
only on the user's express affirmative to an explicit record-this question,
and always as advisory via `wiki-queue-answer --advisory`). The rubric SHALL
carry calibrated worked examples covering at least: a clean package
preference, a data-modeling pattern, a naming convention, an error-handling
philosophy, and a testing strategy classified include; an explicitly one-off
decision and a repo-self-evidencing version pin classified exclude; and a
workflow workaround stated in annoyance, tooling-enforced process etiquette,
and a personal presentation preference classified consent-gated. The rubric
SHALL state that borderline cases lean toward the less-capturing tier and
that user-personal (non-workspace) preferences are recommended to the
personal memory store instead.

#### Scenario: Rubric reference exists with three tiers
- **WHEN** `plugins/s/skills/ask/references/capture-rubric.md` is inspected
- **THEN** it defines the include, exclude, and consent-gated tiers, the
  express-instruction rule for consent-gated capture, and the advisory
  capture mechanics

#### Scenario: Calibrated examples are present
- **WHEN** the rubric's examples are inspected
- **THEN** each named example category appears with its tier and a short
  rationale

### Requirement: Fallback store serves a bare repo
id: oracle-fallback-store

Where no workspace is discoverable from the asking repo and the repo's
resolved content directory exists, the `oracle-lookup` verb's workspace rung
SHALL search the repo-local fallback store that `wiki-show` reports, and
answered-but-undrained queue blocks found there SHALL print as snippets
citable exactly as chain-store blocks are (`queue q-<slug>`).

#### Scenario: Fallback page answers the question
- **GIVEN** a bare repo whose fallback store holds a page settling the
  decision
- **WHEN** the oracle is consulted
- **THEN** the lookup prints that page's snippet cited `[[slug]]` before any
  spec-surface snippet, and the verdict is `ANSWER` citing it

#### Scenario: Fallback answered queue block is citable
- **GIVEN** a bare repo whose fallback store's queue holds a `## q-<slug>`
  block with a non-`pending` answer settling the decision
- **WHEN** the oracle is consulted
- **THEN** the lookup prints the block cited `queue q-<slug>`, and the
  verdict is `ANSWER` citing it

### Requirement: Inline oracle consultation contract
id: oracle-consultation-contract

The plugin SHALL provide the oracle consultation contract at
`plugins/s/skills/ask/references/oracle-contract.md`, at most 120 lines long.
Every oracle consultation — `/s:ask`, `/s:plan`, and the autopilot's driven
sessions — SHALL follow it inline and SHALL spawn no agent. In this
capability, "the oracle" names that consultation. The contract SHALL direct
the consulting skill to run `spec_status.py --root <asking-root>
oracle-lookup <term>...` once per compact question, choosing two to six
distinctive terms from the decision and its options, and at most once more
with alternative terms when the first run finds no evidence. The skill SHALL then
judge the verdict from that output alone. It SHALL take the first rung's
snippet that states a position on the specific decision. It SHALL return
`ANSWER` only then, copying the snippet's citation verbatim onto a `Cited:`
line and quoting the snippet verbatim on an `Evidence:` line. Its default
verdict SHALL be `INSUFFICIENT`: it SHALL NOT answer from model knowledge,
and topical relevance alone SHALL NOT suffice. The contract SHALL keep the
verdict grammar callers branch on: a first non-blank line of exactly `ANSWER`
or `INSUFFICIENT`; an `Authority: advisory` line when the position rests on
an `[advisory]` snippet; and, on `INSUFFICIENT`, the compact question block
and a `Queued:` line. Before queueing, the skill SHALL check the lookup's
not-evidence pending list for an equivalent question and cite it instead of
adding a duplicate. The plugin SHALL NOT ship an oracle agent:
`plugins/s/agents/oracle.md` and `plugins/s/harness/agents/oracle.md` SHALL
be absent.

#### Scenario: Contract carries the judging rules
- **WHEN** `plugins/s/skills/ask/references/oracle-contract.md` is inspected
- **THEN** it names `oracle-lookup`, the default-`INSUFFICIENT` bar, the
  verbatim `Cited:` and `Evidence:` rule, the `Authority: advisory`
  carry-through, the duplicate check, and the two-verdict first-line
  contract, within 120 lines

#### Scenario: No oracle agent ships
- **WHEN** `plugins/s/agents/` and `plugins/s/harness/agents/` are listed
- **THEN** neither holds an `oracle.md`

#### Scenario: A topical snippet yields INSUFFICIENT
- **WHEN** every snippet the lookup prints touches the decision's topic
  without stating a position on it
- **THEN** the contract directs returning `INSUFFICIENT`
