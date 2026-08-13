## ADDED Requirements

### Requirement: Research report format
id: research-report-format

A research report installed at `<content-dir>/research/<slug>/report.md`
SHALL open with a non-empty level-1 title on its first line, SHALL carry a
`## Sources` section holding at least one numbered entry (`N. …`), and SHALL
carry at least one inline citation marker `[n]`; every citation marker
outside fenced code blocks SHALL reference a number present in the sources
list (a bracketed number immediately followed by `(` is a markdown link, not
a marker). This format is enforced at engine install time; a file linked
from an epic's `## Research` section is still validated for existence only
(epic-research-section is unchanged).

#### Scenario: Conforming report is accepted
- **WHEN** a report with a title line, `[1]`-style markers, and a
  `## Sources` section listing source 1 is checked
- **THEN** tooling reports no findings

#### Scenario: Missing sources section is rejected
- **WHEN** a report carries citation markers but no `## Sources` section
- **THEN** tooling reports the missing section as an error

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a report cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a report's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings
