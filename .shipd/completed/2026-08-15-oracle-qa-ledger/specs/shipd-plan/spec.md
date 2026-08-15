## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Oracle-settled decisions stay visible
id: oracle-resolution-visibility
base: 81a0aaeacc9a

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
