## MODIFIED Requirements

### Requirement: Research report validation
id: research-report-validation
base: 1bbfd287ea4f

`spec_lint.py` SHALL provide research report checks callable in-process
(`lint_research(root, slug, errors)`) that always enforce a non-empty
`# <title>` on the report's first line. Where the report carries a citation
signal — a `## Sources` section, or at least one inline `[n]` citation marker
outside fenced code blocks — the checks SHALL additionally enforce the full
citation skeleton: the numbered `## Sources` section, the at-least-one-marker
rule, and citation-marker resolution with fenced code blocks skipped. If the
report carries neither signal, then only the title check SHALL apply and a
titled report SHALL produce no findings. Every finding SHALL name the report
file. Library linting SHALL NOT walk the content directory's `research/`
folder on its own; the checks run only when the emit engine installs a report.

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

#### Scenario: Library lint ignores research files
- **WHEN** `spec_lint.py` lints the library while an invalid file sits under
  the content directory's `research/` folder
- **THEN** no research finding is produced
