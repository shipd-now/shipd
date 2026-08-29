## ADDED Requirements

### Requirement: Supplied document install
id: epic-supplied-document-install

Where the user supplies a context document for the feature that does not
already reside under the content directory's `research/` folder, the
`/s:epic` skill SHALL install it through
`spec_emit.py research <slug> --from <file>` — never by writing into the spec
tree directly — choosing a kebab-case slug derived from the document's
level-1 title, or from its filename when the document carries no title. Where
the document lacks a level-1 title on its first line, the skill SHALL stage a
copy that prepends a `# <title>` derived from the filename and install the
staged copy, leaving the user's original file unmodified. The skill SHALL
then record the installed report in the epic's `## Research` section exactly
as any other consumed research file (research-fed-authoring is unchanged).

#### Scenario: Supplied document is installed and linked
- **GIVEN** the user points epic authoring at a titled markdown document
  outside the content directory
- **WHEN** the epic is authored
- **THEN** the document is installed at the resolved
  `research/<slug>/report.md` via the emit engine and the epic's
  `## Research` section links it

#### Scenario: Untitled document gains a staged title
- **GIVEN** the user supplies a document whose first line is not a level-1
  title
- **WHEN** the skill installs it
- **THEN** the installed report opens with a `# <title>` derived from the
  filename and the user's original file is unchanged

#### Scenario: Already-installed research is not reinstalled
- **GIVEN** the user points epic authoring at a file already under the
  content directory's `research/` folder
- **WHEN** the epic is authored
- **THEN** no install runs and the file is read and linked as before
