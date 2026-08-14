## ADDED Requirements

### Requirement: Video entry point
id: plan-video-entry

Where `/s:plan`'s argument names a recording — a path whose extension is a
recognized video container — or a slug that resolves to an existing ingest
bundle, the skill SHALL obtain a video intent brief before investigating, by
invoking the `/s:video-ingest` skill **by reference** rather than
reimplementing ingestion, passing the recording path or the bundle slug
through unchanged. The resulting brief SHALL be used as an **input to**
investigation, and the codebase-first investigation SHALL still run — the brief
establishes what the speaker wants, the repository still establishes which
capability owns it. Where the argument is neither, the skill SHALL fall through
to its ordinary flow unchanged. The skill SHALL name the installed brief in
user-visible text so its provenance is traceable.

#### Scenario: A recording is ingested before investigation
- **WHEN** `/s:plan` is invoked with a path to a video container
- **THEN** a brief is obtained through the `/s:video-ingest` skill and the
  codebase-first investigation still runs afterwards

#### Scenario: An existing bundle is reused rather than re-ingested
- **WHEN** the argument is a slug resolving to an existing bundle
- **THEN** that bundle's brief is used without re-ingesting the recording

#### Scenario: An ordinary argument is unaffected
- **WHEN** the argument is neither a recognized video path nor a resolvable
  bundle slug
- **THEN** the skill runs its ordinary flow with no ingest attempted

#### Scenario: The brief does not replace reading the repository
- **WHEN** planning proceeds from a brief
- **THEN** the affected capabilities and files are still established by reading
  the repository, not taken from the brief alone

### Requirement: Epic-sized briefs are reported, not emitted
id: plan-video-epic-advisory

Where a brief's intents are too broad to be served by a single change, `/s:plan`
SHALL report that the brief reads as epic-sized, name the intents that drove
that read, recommend `/s:epic`, and stop **without emitting a change**. The
skill SHALL NOT invoke `/s:epic` itself, and SHALL NOT apply a mechanical
threshold — the assessment is a judgement the skill states and the user
settles. Where the brief's intents are within one change's scope, the skill
SHALL proceed to emission as usual.

#### Scenario: A broad brief stops before emission
- **WHEN** a brief's intents are too broad for one change
- **THEN** the skill reports that assessment with the intents behind it,
  recommends `/s:epic`, and installs no change

#### Scenario: The user decides, not the skill
- **WHEN** the skill judges a brief epic-sized
- **THEN** it does not invoke `/s:epic` and leaves the decision to the user

#### Scenario: A focused brief proceeds normally
- **WHEN** a brief's intents fit within a single change
- **THEN** the skill continues through the depth gate to emission without
  raising the epic recommendation
