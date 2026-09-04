## MODIFIED Requirements

### Requirement: Oracle user documentation
id: oracle-user-docs
base: 03f54b794f1d

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
unconditional write.

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
