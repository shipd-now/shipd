## ADDED Requirements

### Requirement: Video-brief-fed epic authoring
id: video-fed-epic-authoring

Where a video intent brief is supplied for the feature — a bundle slug the user
names, or a brief the epic under authoring already links — the `/s:epic` skill
SHALL read that brief through the engine (`spec_status.py cat video <slug>`) as
pre-investigation context before its question round, and SHALL record every
brief it read as a link entry in the epic's `## Video` section. The brief SHALL
be an input to investigation and never a replacement for it: the codebase-first
rule still binds, so the affected capabilities and the decomposition seams are
still established by reading the repository. The skill SHALL NOT invent entries
for briefs it did not read, and an epic authored with no brief SHALL carry no
`## Video` section.

#### Scenario: A supplied brief is consumed and recorded
- **GIVEN** the user points epic authoring at the bundle slug `kickoff-call`
- **WHEN** the epic is emitted
- **THEN** its `## Video` section links `.shipd/video/kickoff-call/brief.md` and
  its Decisions reflect context drawn from that brief

#### Scenario: No brief means no section
- **WHEN** an epic is authored with no video brief supplied
- **THEN** the emitted epic carries no `## Video` section

#### Scenario: The brief does not replace reading the repository
- **WHEN** epic authoring proceeds from a brief
- **THEN** the member decomposition and the affected capabilities are still
  established by reading the repository, not taken from the brief alone

#### Scenario: An unread brief is never linked
- **WHEN** a brief exists under the content directory's `video/` folder but was
  not read for this feature
- **THEN** the emitted epic carries no entry for it

### Requirement: Epic authoring does not ingest recordings
id: epic-no-recording-ingest

If the argument given to `/s:epic` names a recording rather than an installed
intent brief, then the skill SHALL NOT ingest it and SHALL report that
`/s:video-ingest` produces the brief first, leaving the ingest surface in one
place. `/s:epic` SHALL consume only briefs already installed under the content
directory's `video/` folder.

#### Scenario: A recording is reported, not ingested
- **WHEN** `/s:epic` is invoked with a path to a video container
- **THEN** no ingest is performed and the skill directs the user to
  `/s:video-ingest` to produce the brief first

#### Scenario: An installed brief is consumed normally
- **WHEN** `/s:epic` is invoked with a slug naming an installed brief
- **THEN** the brief is read and authoring proceeds without any ingest
