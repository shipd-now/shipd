## ADDED Requirements

### Requirement: Base-hash verb
id: base-hash-verb

The status CLI SHALL provide `base-hash <capability> <requirement-id>`,
printing to stdout the content hash of that requirement as it stands in the
resolved master library, and exiting zero. The verb SHALL resolve the master
and compute the hash through the merge engine's own primitives — the same
master resolution and content-hash function `check-base` and the merge-time
base comparison use — so a hash this verb prints can never disagree with the
hash the merge later compares against. The verb SHALL be strictly read-only:
it SHALL write no file and SHALL change no status. If the named capability
has no master spec, or the named requirement id is absent from it, then the
verb SHALL report a single `Error: <reason>` line on stderr naming what was
not found and SHALL exit non-zero; a missing or extra argument SHALL print
usage on stderr and exit 2.

#### Scenario: A known requirement's hash is printed
- **GIVEN** a master library carrying a capability with a requirement id
- **WHEN** `base-hash <capability> <requirement-id>` runs
- **THEN** stdout carries that requirement's content hash and the exit code
  is zero

#### Scenario: The hash matches what the merge compares against
- **WHEN** the verb's output for a requirement is compared with the content
  hash the engine computes for that same requirement
- **THEN** the two are identical

#### Scenario: An unknown capability fails loudly
- **WHEN** `base-hash no-such-capability some-id` runs
- **THEN** stderr carries a single line beginning `Error: ` and the exit code
  is non-zero

#### Scenario: An unknown requirement id fails loudly
- **GIVEN** a capability whose master does not declare the requested id
- **WHEN** `base-hash <capability> no-such-id` runs
- **THEN** stderr carries a single line beginning `Error: ` naming the id and
  the exit code is non-zero

#### Scenario: A missing argument is a usage error
- **WHEN** the verb runs with no requirement id
- **THEN** usage is printed on stderr and the exit code is 2

#### Scenario: The verb changes nothing
- **GIVEN** a repository whose content directory is unmodified
- **WHEN** the verb runs against any capability
- **THEN** no file under the content directory is created, modified, or
  deleted
