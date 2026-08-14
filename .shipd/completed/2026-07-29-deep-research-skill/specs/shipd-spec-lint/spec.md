## ADDED Requirements

### Requirement: Research report validation
id: research-report-validation

`spec_lint.py` SHALL provide research report checks callable in-process
(`lint_research(root, slug, errors)`) enforcing the research report format —
the title line, the numbered `## Sources` section, the at-least-one-marker
rule, and citation-marker resolution with fenced code blocks skipped — with
every finding naming the report file. Library linting SHALL NOT walk the
content directory's `research/` folder on its own; the checks run only when
the emit engine installs a report.

#### Scenario: Clean report passes
- **WHEN** the research checks run on a report with a title, resolving
  markers, and a numbered sources list
- **THEN** no findings are produced

#### Scenario: Unresolved marker is a named finding
- **WHEN** the research checks run on a report citing `[4]` over three listed
  sources
- **THEN** a finding names the report file and the `[4]` marker

#### Scenario: Library lint ignores research files
- **WHEN** `spec_lint.py` lints the library while an invalid file sits under
  the content directory's `research/` folder
- **THEN** no research finding is produced
