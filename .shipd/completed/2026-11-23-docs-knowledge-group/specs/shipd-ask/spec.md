## MODIFIED Requirements

### Requirement: Oracle user documentation
id: oracle-user-docs
base: a602655b1083

The repository SHALL provide `docs/oracle.md`, the main page for the oracle
and `/s:ask`, conforming to the shipd documentation standard:
`<!-- doc-type: reference -->` as its first line and a total line count
within the reference cap.

The page SHALL follow the main-page shape. Its opening and a `## The ladder`
section say what the oracle is, and that section SHALL hold a diagram of the
read → oracle → human ladder with the answer-capture loop. A
`## When to use it` section SHALL follow, then a `## How to run it` section
covering the `/s:ask` invocation and the automatic consultation by `/s:plan`,
then a closing `## Reference` section. The page SHALL carry no `## See also`
section.

`## Reference` SHALL hold: the two verdicts each shown with an example
(`ANSWER` with `Cited:` and `Evidence:` lines; `INSUFFICIENT` with its queued
question); the definitive-evidence answering bar; the classified capture
loop; and the correction path via `/s:teach`, stated briefly with a link to
`docs/wiki.md`.

The page SHALL document the advisory variant of `ANSWER` — an
`Authority: advisory` line after the position, shown in an example — stating
that an advisory answer is surfaced as a recommended, citable default the
user can accept or override, never a silent settlement, and that an `ANSWER`
without the line is binding.

The page SHALL document the classified capture loop: a typed answer is
classified against the capture durability rubric before any queue write —
include-tier answers captured via `wiki-queue-answer`, exclude-tier answers
discarding their pending block via `wiki-queue-discard` with nothing stored,
and consent-gated answers recorded as advisory only on the user's express
record-this instruction. It SHALL point a preference about the user to
`docs/memory.md` in one linked sentence.

The ladder diagram SHALL be a `mermaid` code fence — not ASCII box-drawing
art — so the published docs site renders it natively, and its capture path
SHALL reflect the classification rather than an unconditional write.

The page SHALL name engine verbs as bare verb names and SHALL NOT name an
engine script path.

#### Scenario: Guide covers the loop
- **WHEN** `docs/oracle.md` is inspected
- **THEN** it holds a ladder-and-capture-loop diagram, an `ANSWER` example
  with `Cited:` and `Evidence:` lines, an `INSUFFICIENT` example, and names
  `/s:teach` as the correction path

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/oracle.md` are listed
- **THEN** they are `## The ladder`, `## When to use it`, `## How to run it`,
  and `## Reference`, in that order, and no `## See also` heading remains

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

#### Scenario: Page links its neighbours
- **WHEN** the relative links of `docs/oracle.md` are followed
- **THEN** the correction section links `wiki.md`, the capture section links
  `memory.md`, and every link resolves

#### Scenario: Guide carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/oracle.md`
- **THEN** it exits 0 with the file marked `reference`, and the page names no
  `spec_status.py` or `spec_emit.py` path
