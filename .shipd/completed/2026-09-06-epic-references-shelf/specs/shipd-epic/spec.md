## MODIFIED Requirements

### Requirement: Supplied document install
id: epic-supplied-document-install
base: b19154e197b3

Where the user supplies a context document for the feature that does not
already reside under the content directory's `research/`, `video/`, or
`docs/` folder, the `/s:epic` skill SHALL install it through
`spec_emit.py docs <slug> --from <file>` — never by writing into the spec
tree directly — choosing a kebab-case slug derived from the document's
level-1 title, or from its filename when the document carries no title.
Where the document lacks a level-1 title on its first line, the skill SHALL
stage a copy that prepends a `# <title>` derived from the filename and
install the staged copy, leaving the user's original file unmodified. The
skill SHALL then record the installed document as a link entry in the epic's
`## References` section, creating the section when absent. A supplied file
already residing under one of those three folders SHALL be read and linked
without reinstalling.

#### Scenario: Supplied document is installed and linked
- **GIVEN** the user points epic authoring at a titled markdown document
  outside the content directory
- **WHEN** the epic is authored
- **THEN** the document is installed at the resolved `docs/<slug>/doc.md`
  via the emit engine and the epic's `## References` section links it

#### Scenario: Untitled document gains a staged title
- **GIVEN** the user supplies a document whose first line is not a level-1
  title
- **WHEN** the skill installs it
- **THEN** the installed document opens with a `# <title>` derived from the
  filename and the user's original file is unchanged

#### Scenario: Already-installed artifacts are not reinstalled
- **GIVEN** the user points epic authoring at a file already under the
  content directory's `research/`, `video/`, or `docs/` folder
- **WHEN** the epic is authored
- **THEN** no install runs and the file is read and linked as before

### Requirement: Research-fed epic authoring
id: research-fed-authoring
base: dac29b543db1

Where research is supplied for the feature — reports the user names, or
files the epic under authoring already links — the `/s:epic` skill SHALL
read those research files as pre-investigation context before its question
round, and SHALL record every consumed report as a link entry in the epic's
`## References` section. Where the epic under authoring already carries a
`## Research` section, the skill MAY extend that section in place instead —
the legacy section stays valid and is never migrated. The skill SHALL NOT
invent entries for files it did not read, and epics for features with no
research SHALL carry no entry for one in either section.

#### Scenario: Supplied research is consumed and recorded
- **GIVEN** the user points epic authoring at
  `.shipd/research/payment-apis/report.md`
- **WHEN** the epic is emitted
- **THEN** its `## References` section links that report and the epic's
  Decisions reflect context drawn from it

#### Scenario: A legacy Research section is extended in place
- **GIVEN** an epic under authoring already carries a `## Research` section
- **WHEN** a further report is consumed
- **THEN** recording it as a `## Research` entry is valid and no migration
  to `## References` is forced

#### Scenario: No research means no entry
- **WHEN** an epic is authored with no research supplied or discovered
- **THEN** the emitted epic carries no research link entry

### Requirement: Video-brief-fed epic authoring
id: video-fed-epic-authoring
base: ff5c641b8f8e

Where a video intent brief is supplied for the feature — a bundle slug the
user names, or a brief the epic under authoring already links — the
`/s:epic` skill SHALL read that brief through the engine
(`spec_status.py cat video <slug>`) as pre-investigation context before its
question round, and SHALL record every brief it read as a link entry in the
epic's `## References` section; where the epic under authoring already
carries a `## Video` section, the skill MAY extend that section in place —
the legacy section stays valid and is never migrated. The brief SHALL be an
input to investigation and never a replacement for it: the codebase-first
rule still binds, so the affected capabilities and the decomposition seams
are still established by reading the repository. The skill SHALL NOT invent
entries for briefs it did not read, and an epic authored with no brief SHALL
carry no brief link entry.

#### Scenario: A supplied brief is consumed and recorded
- **GIVEN** the user points epic authoring at the bundle slug `kickoff-call`
- **WHEN** the epic is emitted
- **THEN** its `## References` section links
  `.shipd/video/kickoff-call/brief.md` and its Decisions reflect context
  drawn from that brief

#### Scenario: No brief means no entry
- **WHEN** an epic is authored with no video brief supplied
- **THEN** the emitted epic carries no brief link entry

#### Scenario: The brief does not replace reading the repository
- **WHEN** epic authoring proceeds from a brief
- **THEN** the member decomposition and the affected capabilities are still
  established by reading the repository, not taken from the brief alone

#### Scenario: An unread brief is never linked
- **WHEN** a brief exists under the content directory's `video/` folder but
  was not read for this feature
- **THEN** the emitted epic carries no entry for it
