## MODIFIED Requirements

### Requirement: Research report format
id: research-report-format
base: 738193e6d4db

A research report installed at `<content-dir>/research/<slug>/report.md`
SHALL open with a non-empty level-1 title on its first line. Where the report
carries a citation signal — a `## Sources` section, or any inline `[n]`
citation marker outside fenced code blocks — it SHALL satisfy the full
citation skeleton: a `## Sources` section holding at least one numbered entry
(`N. …`), at least one inline `[n]` marker, and every marker outside fenced
code blocks referencing a number present in the sources list (a bracketed
number immediately followed by `(` is a markdown link, not a marker). A titled
report carrying neither signal SHALL be accepted — the document's origin never
gates installation. This format is enforced at engine install time; a file
linked from an epic's `## Research` section is still validated for existence
only (epic-research-section is unchanged).

#### Scenario: Conforming cited report is accepted
- **WHEN** a report with a title line, `[1]`-style markers, and a
  `## Sources` section listing source 1 is checked
- **THEN** tooling reports no findings

#### Scenario: Uncited titled document is accepted
- **WHEN** a titled report with no `## Sources` section and no `[n]` markers
  is checked
- **THEN** tooling reports no findings

#### Scenario: Markers without a sources section are rejected
- **WHEN** a report carries citation markers but no `## Sources` section
- **THEN** tooling reports the missing section as an error

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a report cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a report's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings
