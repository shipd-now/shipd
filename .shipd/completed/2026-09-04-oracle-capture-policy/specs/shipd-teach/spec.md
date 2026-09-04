## MODIFIED Requirements

### Requirement: Queue draining
id: teach-queue-drain
base: 0e830c35b756

The skill SHALL drain answered queue entries: every `## q-` block in
`queue.md` whose `Answer:` line is not `pending` SHALL be distilled into wiki
page content and removed from the staged `queue.md` in the same ingest, with
the run's log entry naming each drained `q-<slug>`. Where a drained block's
`Answer:` value begins with the `advisory: ` prefix, the distilled page
content SHALL carry an `Authority: advisory` line, preserving the advisory
standing so the oracle relays it as a recommendation rather than a
settlement; answers without the prefix distill as binding pages with no
`Authority:` line, as before. Blocks whose `Answer:` is `pending` SHALL be
left untouched.

#### Scenario: Answered entry is drained
- **WHEN** a run finds a queue block with a supplied answer
- **THEN** after the ingest the answer's content lives in a wiki page, the
  block is gone from `queue.md`, and the log entry names its `q-<slug>`

#### Scenario: Advisory answer drains into an advisory page
- **GIVEN** a queue block whose answer line reads
  `- Answer: advisory: always run the unlock first`
- **WHEN** a run drains it
- **THEN** the distilled page carries an `Authority: advisory` line and the
  block is gone from `queue.md`

#### Scenario: Pending entries survive
- **WHEN** a run ingests while `queue.md` holds `Answer: pending` blocks
- **THEN** those blocks remain in `queue.md` unchanged
