## ADDED Requirements

### Requirement: Docs document validation
id: docs-document-validation

`spec_lint.py` SHALL provide docs document checks callable in-process
(`lint_docs(root, slug, errors)`) that enforce exactly one rule on the
document at `<content-dir>/docs/<slug>/doc.md`: a non-empty `# <title>` on
the document's first line. The checks SHALL NOT demand any citation
skeleton, header metadata, or section structure — an installed document's
body is free-form, so a supplied document never fails on a provenance or
structure grammar it did not claim. Every finding SHALL name the document
file. If the document file is missing, then the checks SHALL report that as
a finding naming the expected path. Library linting SHALL NOT walk the
content directory's `docs/` folder on its own, and the checks SHALL have no
`spec_lint.py` command-line mode; they run only when the emit engine
installs a document.

#### Scenario: Titled free-form document passes
- **WHEN** the docs checks run on a document whose first line is a non-empty
  `# <title>` and whose body is arbitrary markdown, including `[1]`-style
  bracket markers and no `## Sources` section
- **THEN** no findings are produced

#### Scenario: Untitled document is rejected
- **WHEN** the docs checks run on a document whose first line is not a
  non-empty `# <title>`
- **THEN** a finding names the document file and the expected title line

#### Scenario: Library lint ignores docs files
- **WHEN** `spec_lint.py` lints the library while an untitled file sits
  under the content directory's `docs/` folder
- **THEN** no docs finding is produced
