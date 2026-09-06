## ADDED Requirements

### Requirement: Docs document format
id: docs-document-format

A document installed at `<content-dir>/docs/<slug>/doc.md` SHALL open with a
non-empty level-1 title (`# <title>`) on its first line; its remaining
content SHALL be free-form markdown with no further structural demands — no
citation skeleton, no header metadata block, no required sections — so any
supplied document (strategy notes, meeting minutes, an API excerpt) installs
without pretending to a grammar it does not have. This format is enforced at
engine install time only; the `docs/` folder is never walked by library
linting.

#### Scenario: Titled document is accepted
- **WHEN** a document opening with `# Payments strategy` followed by
  arbitrary markdown is checked
- **THEN** tooling reports no findings

#### Scenario: Missing title is rejected
- **WHEN** a document whose first line is body prose is checked
- **THEN** tooling reports the missing title line as an error naming the
  document file

#### Scenario: Bracket markers never trip a citation check
- **WHEN** a titled document containing `[3]`-style footnote markers and no
  `## Sources` section is checked
- **THEN** tooling reports no findings
