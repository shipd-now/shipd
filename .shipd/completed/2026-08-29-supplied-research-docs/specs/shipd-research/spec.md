## MODIFIED Requirements

### Requirement: Cited report composition
id: research-report-content
base: 965247acb437

The `/s:research` skill SHALL compose the report with a summary, themed
findings sections, a gaps-and-caveats section, and a numbered `## Sources`
list, and SHALL cite every load-bearing claim with an inline `[n]` marker that
maps to a listed source. The skill SHALL place a provenance note directly
under the title line stating the report was prepared by the shipd research
skill (e.g. `> Prepared by the shipd research skill (/s:research).`), so a
skill-composed report stays distinguishable from a supplied document once the
engine accepts uncited installs. If a claim cannot be anchored to a fetched
source, then the skill SHALL place it in the gaps-and-caveats section instead
of asserting it as a cited finding.

#### Scenario: Composed report carries the shape and citations
- **WHEN** the skill composes a report from extracted findings
- **THEN** the report holds a summary, themed findings, gaps and caveats, and
  numbered sources, with `[n]` markers on the load-bearing claims

#### Scenario: Composed report is provenance-labeled
- **WHEN** the skill composes a report
- **THEN** a provenance note naming the shipd research skill sits directly
  under the title line

#### Scenario: Unanchored claim is downgraded
- **WHEN** a claim survives extraction with no fetched source anchoring it
- **THEN** it appears under gaps and caveats rather than as a cited finding
