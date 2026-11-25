## MODIFIED Requirements

### Requirement: Enrichment gap diagnosis
id: enrichment-gap-diagnosis
base: 1a9f6c2a71b6

While in enrichment mode, the skill SHALL read the change's artifacts through
the engine's `cat change` verb and treat the plan's `## Context insufficient`
findings as the work agenda. It SHALL resolve every codebase-answerable
finding directly by editing the installed artifacts in the located change
directory — refreshing stale `base:` hashes against the current master
requirement and reconciling the delta, correcting dangling task file
references or declaring the ones the task creates, and replacing placeholder
markers with decisions grounded in the repository — and SHALL put to the user
only findings the repository cannot answer, batched under the fast-path
typed-round contract with a context brief. The skill SHALL NOT ask about
anything discoverable from the repository. The skill SHALL NOT remove the
backticks from a repository path, or create placeholder directories, to clear
a file-reference finding.

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

#### Scenario: A new path is declared, not hidden
- **WHEN** the dangling-reference bullets of `enrichment.md` and the harness
  copy of the plan reference are read
- **THEN** each says to declare a path the task creates with `Create` directly
  before it, and forbids removing backticks or creating placeholder directories

## ADDED Requirements

### Requirement: Task path citation rules
id: task-path-citation

`authoring.md` SHALL state, under its Tasks heading, that a task cites each
repository path in backticks as the full path from the repository root, that
`Create` or `Add` goes directly before a path the task creates, and that
backticks are never removed from a repository path to satisfy the gate.

#### Scenario: The Tasks part carries the citation rules
- **WHEN** the Tasks part of `authoring.md` is read
- **THEN** it states the full-path rule, the `Create` or `Add` rule, and the
  prohibition on removing backticks
