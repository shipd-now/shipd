## MODIFIED Requirements

### Requirement: Video entry point
id: plan-video-entry
base: 527d04e3782c

Where `/s:plan`'s argument names a recording — a path whose extension is a
recognized video container — or a slug that resolves to an existing ingest
bundle, the skill SHALL obtain a video intent brief before investigating, by
invoking the `/s:video-ingest` skill **by reference** rather than
reimplementing ingestion, passing the recording path or the bundle slug
through unchanged. The resulting brief SHALL be used as an **input to**
investigation, and the codebase-first investigation SHALL still run — the brief
establishes what the speaker wants, the repository still establishes which
capability owns it. Where the brief carries a `Project:` line **and** the
planning repository resolves to a declared project in the workspace registry,
the skill SHALL compare the two and, on a mismatch, report both project names
and stop without emitting a change, unless the invocation carries an explicit
`--cross-project` override, in which case it SHALL proceed and say so. Where
either side is absent there is nothing to compare and the skill SHALL proceed
without a project check. Where the argument is neither a recording nor a bundle
slug, the skill SHALL fall through to its ordinary flow unchanged. The skill
SHALL name the installed brief in user-visible text so its provenance is
traceable.

#### Scenario: A recording is ingested before investigation
- **WHEN** `/s:plan` is invoked with a path to a video container
- **THEN** a brief is obtained through the `/s:video-ingest` skill and the
  codebase-first investigation still runs afterwards

#### Scenario: An existing bundle is reused rather than re-ingested
- **WHEN** the argument is a slug resolving to an existing bundle
- **THEN** that bundle's brief is used without re-ingesting the recording

#### Scenario: A foreign project stops the plan
- **WHEN** the brief carries a `Project:` naming a different declared project
  than the planning repository resolves to
- **THEN** the skill reports both project names and ends the turn without
  emitting a change

#### Scenario: The override proceeds deliberately
- **WHEN** the same mismatch occurs and the invocation carries
  `--cross-project`
- **THEN** the skill proceeds through its ordinary flow and states in
  user-visible text that the project check was overridden

#### Scenario: An unresolvable project side skips the check
- **WHEN** the brief carries no `Project:` line, or the planning repository
  resolves to no declared project
- **THEN** no project comparison is attempted and planning proceeds

#### Scenario: An ordinary argument is unaffected
- **WHEN** the argument is neither a recognized video path nor a resolvable
  bundle slug
- **THEN** the skill runs its ordinary flow with no ingest attempted

#### Scenario: The brief does not replace reading the repository
- **WHEN** planning proceeds from a brief
- **THEN** the affected capabilities and files are still established by reading
  the repository, not taken from the brief alone
