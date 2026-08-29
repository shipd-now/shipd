## MODIFIED Requirements

### Requirement: Oracle user documentation
id: oracle-user-docs
base: 4edd52b714ef

The repository SHALL provide `docs/oracle.md`, a user-facing guide to the
oracle that includes a diagram of the read → oracle → human ladder with the
answer-capture loop, the two verdicts each shown with an example
(`ANSWER` with `Cited:` and `Evidence:` lines; `INSUFFICIENT` with its queued
question), the definitive-evidence answering bar, and the correction path via
`/s:teach`. The ladder diagram SHALL be a `mermaid` code fence — not ASCII
box-drawing art — so the published docs site renders it natively.

#### Scenario: Guide covers the loop
- **WHEN** `docs/oracle.md` is inspected
- **THEN** it holds a ladder-and-capture-loop diagram, an `ANSWER` example
  with `Cited:` and `Evidence:` lines, an `INSUFFICIENT` example, and names
  `/s:teach` as the correction path

#### Scenario: Ladder diagram is mermaid
- **WHEN** the ladder diagram in `docs/oracle.md` is inspected
- **THEN** it is a `mermaid` code fence containing the three rungs (read,
  oracle, human), the `ANSWER` and `INSUFFICIENT` verdict branches, and the
  capture loop back to the oracle rung, and `docs/oracle.md` contains no
  box-drawing characters
