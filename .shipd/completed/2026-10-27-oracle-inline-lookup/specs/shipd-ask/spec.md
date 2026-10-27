## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Ask skill entry
id: ask-skill
base: 6d566594c98c
Dropped: Skill relays the oracle verdict
Dropped: Insufficient verdict defers to the user

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
base: 6bfa4ab32330

Every question put to the oracle — and every question the oracle queues —
SHALL be one decision-ready unit carrying the decision, concrete options, and
the asker's recommendation, never a raw trace or an open-ended essay prompt.
Both `plugins/s/skills/ask/references/oracle-contract.md` and
`plugins/s/skills/ask/SKILL.md` SHALL state this contract.

#### Scenario: Both surfaces carry the contract
- **WHEN** the oracle contract reference and the ask SKILL.md are inspected
- **THEN** each states the decision/options/recommendation compact-question
  shape

### Requirement: Fallback store serves a bare repo
id: oracle-fallback-store
base: f78054299bf2

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

## REMOVED Requirements

### Requirement: Oracle agent contract
id: oracle-agent-contract
base: 28a229f143db
Reason: The `s:oracle` subagent cost about 49K tokens per consultation, most of it fixed agent overhead, so it is retired in favour of an inline engine verb.
Migration: The search ladder and its citation markers move to spec-status `oracle-lookup-verb`; the judging rules and verdict grammar move to `oracle-consultation-contract` above, which every caller follows inline.
