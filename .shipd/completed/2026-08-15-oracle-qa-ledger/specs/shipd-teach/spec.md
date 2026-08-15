## ADDED Requirements

### Requirement: Ledger-entry reference mode
id: teach-qa-reference

When the invocation argument matches `<change> Q<n>`, the skill SHALL bypass
the distillation sweep: it SHALL resolve the change through the engine's
`cat change` read (covering planned and archived-completed changes), print the
referenced `### Q<n>:` ledger entry in full so the user sees exactly what was
asked and answered, and interview the user for the corrected standing
position. The skill SHALL then install the correction through the staged wiki
emit — updating the page an `ANSWER` entry's `**Cited:**` field names when one
exists rather than minting a duplicate, preserving the user's correction
verbatim as a dated `sources/` file, and draining the queue block named by an
`INSUFFICIENT` entry's `**Queued:**` field in the same ingest when that block
is still queued. If the change cannot be resolved or the referenced entry does
not exist, then the skill SHALL report that and stop without writing.

#### Scenario: Entry is shown and the correction lands on the cited page
- **WHEN** `/s:teach dark-mode-toggle Q1` names an `ANSWER` entry citing
  `[[logging-conventions]]` and the user supplies a corrected position
- **THEN** the skill prints the entry in full and the staged emit updates
  `[[logging-conventions]]` with the corrected standing position

#### Scenario: Queued entry is drained with the correction
- **WHEN** the referenced entry carries `**Queued:** q-report-format` and that
  block is still in the wiki queue
- **THEN** the ingest drains `q-report-format` alongside installing the
  correction

#### Scenario: Unresolvable reference stops without writing
- **WHEN** the argument names a change with no `Q<n>` entry of that number
- **THEN** the skill reports the missing entry and writes nothing
