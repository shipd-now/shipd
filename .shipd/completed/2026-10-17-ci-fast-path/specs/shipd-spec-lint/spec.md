## MODIFIED Requirements

### Requirement: Research report validation
id: research-report-validation
base: 4576170774d5
Dropped: Library lint ignores research files

`spec_lint.py` SHALL provide research report checks callable in-process
(`lint_research(root, slug, errors)`) that always enforce a non-empty
`# <title>` on the report's first line. Where the report carries a citation
signal — a `## Sources` section, or at least one inline `[n]` citation marker
outside fenced code blocks — the checks SHALL additionally enforce the full
citation skeleton: the numbered `## Sources` section, the at-least-one-marker
rule, and citation-marker resolution with fenced code blocks skipped. If the
report carries neither signal, then only the title check SHALL apply and a
titled report SHALL produce no findings. Every finding SHALL name the report
file. Library linting SHALL run these checks on every
`<content-dir>/research/<slug>/report.md` it finds, skipping a slug directory
that holds no `report.md`, so CI validates reports without the emit engine.

#### Scenario: Uncited titled document passes
- **WHEN** the research checks run on a report whose first line is a
  non-empty `# <title>` and which carries no `## Sources` section and no
  inline `[n]` markers
- **THEN** no findings are produced

#### Scenario: Cited report is still fully checked
- **WHEN** the research checks run on a report citing `[4]` over three listed
  sources
- **THEN** a finding names the report file and the `[4]` marker

#### Scenario: Markers without a sources section are still rejected
- **WHEN** the research checks run on a report carrying inline `[n]` markers
  but no `## Sources` section
- **THEN** a finding reports the missing `## Sources` section

#### Scenario: Library lint checks research files
- **WHEN** `spec_lint.py` lints the library while an untitled
  `research/broken/report.md` exists
- **THEN** a finding names that report file

### Requirement: Docs document validation
id: docs-document-validation
base: dc00c23340ce
Dropped: Library lint ignores docs files

`spec_lint.py` SHALL provide docs document checks callable in-process
(`lint_docs(root, slug, errors)`) that enforce exactly one rule on the
document at `<content-dir>/docs/<slug>/doc.md`: a non-empty `# <title>` on
the document's first line. The checks SHALL NOT demand any citation
skeleton, header metadata, or section structure — an installed document's
body is free-form, so a supplied document never fails on a provenance or
structure grammar it did not claim. Every finding SHALL name the document
file. If the document file is missing, then the checks SHALL report that as
a finding naming the expected path. Library linting SHALL run these checks on
every `<content-dir>/docs/<slug>/` directory that holds a `doc.md`, and the
checks SHALL have no `spec_lint.py` command-line mode.

#### Scenario: Titled free-form document passes
- **WHEN** the docs checks run on a document whose first line is a non-empty
  `# <title>` and whose body is arbitrary markdown, including `[1]`-style
  bracket markers and no `## Sources` section
- **THEN** no findings are produced

#### Scenario: Untitled document is rejected
- **WHEN** the docs checks run on a document whose first line is not a
  non-empty `# <title>`
- **THEN** a finding names the document file and the expected title line

#### Scenario: Library lint checks docs files
- **WHEN** `spec_lint.py` lints the library while an untitled
  `docs/broken/doc.md` exists
- **THEN** a finding names that document file

#### Scenario: A repo without research or docs lints as before
- **WHEN** `spec_lint.py` lints a library whose content directory has no
  `research/` or `docs/` folder
- **THEN** no research or docs finding is produced
