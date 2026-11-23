## MODIFIED Requirements

### Requirement: Questions-and-answers ledger in the emitted plan
id: plan-qa-ledger
base: 469f52310a15

When at least one oracle consultation ran while planning a change, the emitted
`plan.md` SHALL carry a `## Questions and answers` section recording every
consultation of that planning session as a `### Q<n>: <one-line question
summary>` entry, numbered sequentially from `Q1` in consultation order. Each
entry SHALL carry the full compact question (decision, options,
recommendation), the verdict (`ANSWER` or `INSUFFICIENT`), an
`Answered by:` property holding `ORACLE` or `USER` placed directly above the
answer, and the answer in full — the oracle's position for `ANSWER`, the
user's typed resolution for `INSUFFICIENT`; a headless session SHALL instead
record the default it adopted on `INSUFFICIENT` as `ASSUMPTION`, with that
default as the answer, and a deferring `/s:epic-grill` planner SHALL record the
provisional `PLANNER`; an `ANSWER` entry SHALL carry the
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

#### Scenario: A headless default is recorded as an assumption
- **WHEN** a headless session gets `INSUFFICIENT` from the oracle and adopts its recommended default
- **THEN** the entry carries `**Verdict:** INSUFFICIENT`, `**Answered by:** ASSUMPTION` and the adopted default as its answer
