## ADDED Requirements

### Requirement: Base-hash computation goes through the engine verb
id: base-hash-through-the-engine

The plan skill's emission reference SHALL document computing a MODIFIED or
REMOVED entry's `base:` hash as a call to the status CLI's `base-hash` verb,
rather than as an inline script the planner retypes. The documented command
SHALL be executable exactly as written — a reader SHALL be able to copy it,
substitute the capability and requirement id, and obtain the hash — and the
reference SHALL carry no inline snippet that reads the master spec on the
same stream as its own program text, which cannot run. A test SHALL guard
this by **executing** the documented command and comparing its output against
the engine's own content hash for that requirement, never by matching the
command's text alone, since a textual match would pass on a command that
still could not run.

#### Scenario: The reference names the verb
- **WHEN** the emission reference's base-hash section is read
- **THEN** it documents the status CLI's `base-hash` verb as the way to
  obtain the hash, and carries no inline program competing with the spec text
  for standard input

#### Scenario: The documented command runs as written
- **WHEN** the command the reference documents is executed against a real
  capability and requirement id
- **THEN** it exits zero and prints that requirement's content hash

#### Scenario: The guard executes rather than pattern-matches
- **WHEN** the test guarding the reference is inspected
- **THEN** it runs the documented command and compares the result with the
  engine's content hash for that requirement
